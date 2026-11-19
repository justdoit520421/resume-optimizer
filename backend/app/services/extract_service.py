# 简历文本提取工具：支持 PDF / Word
import io
import re
import unicodedata
from app.exceptions import BizException
from app.response import BizCode


# CJK 部首补充区（U+2E80–U+2EFF）无 NFKC 分解，需手工映射（仅收高置信度常用字）
_RADICAL_MANUAL_MAP = {
    0x2ED3: "长",  # ⻓ C-SIMPLIFIED LONG
    0x2ED4: "门",  # ⻔ C-SIMPLIFIED GATE
    0x2EDA: "页",  # ⻚ C-SIMPLIFIED LEAF
}


def normalize_cjk(text: str) -> str:
    """把康熙部首/部首补充区码位归一化为标准 CJK 汉字。

    部分 PDF 生成器会把常规汉字映射到部首区块（如 '⼤' U+2F24 而非 '大' U+5927），
    这些码位在导出字体中缺字形，渲染为空白。
    - 康熙部主区（U+2F00–U+2FD5）：NFKC 有兼容分解，直接归一化
    - 部首补充区（U+2E80–U+2EFF）：无 NFKC 分解，走手工映射表
    仅处理部首区块，避免误伤全角标点。
    """
    out = []
    for ch in text:
        cp = ord(ch)
        if 0x2F00 <= cp <= 0x2FD5:
            ch = unicodedata.normalize("NFKC", ch)
        elif cp in _RADICAL_MANUAL_MAP:
            ch = _RADICAL_MANUAL_MAP[cp]
        out.append(ch)
    return "".join(out)


# ---------------- 文本清洗（提取与导出共用） ----------------

# 常见简历章节标题
_SECTION_KEYS = (
    "个人信息", "基本信息", "求职意向", "教育背景", "教育经历",
    "工作经历", "实习经历", "项目经历", "项目经验", "校园经历", "在校经历",
    "技能", "专业技能", "自我评价", "证书", "荣誉", "获奖经历", "语言能力",
)

# 全角标点：其前后不应出现多余空格
_FW_PUNCT_RE = "[：，。、；！？（）「」『』《》〈〉【】〔〕]"

# 句末标点：出现在行尾说明该行语义完整，不应与下一行合并
_SENT_END = "。！？；!?;"

_DATE_RANGE_RE = re.compile(
    r"\d{4}\s*[-/年.]\s*\d{1,2}\s*([-/月.]\s*\d{1,2})?\s*(至|到|~|-|—)\s*\d{4}"
)
_DATE_END_RE = re.compile(r"\d{4}\s*[-/年.]\s*\d{1,2}\s*([-/月.]\s*\d{1,2})?\s*$")
_LABEL_RE = re.compile(r"^[^\s：:]{1,12}[：:]")          # 形如「手机：」「期望薪资：」
_BULLET_RE = re.compile(r"^[·•●▪◦]\s*")                  # 项目符号
_NUMBER_RE = re.compile(r"^\d{1,2}\s*[.、)）]")           # 序号 1. / 2、
_DATE_START_RE = re.compile(r"^\d{4}\s*[-/年.]")          # 行首日期


def is_section(line: str) -> bool:
    """判断一行是否为章节标题（容忍尾部冒号 / 空格，或标题前缀）"""
    key = line.strip().rstrip("：: ").strip()
    if key in _SECTION_KEYS:
        return True
    return len(key) <= 24 and any(key.startswith(k) for k in _SECTION_KEYS)


def _normalize_spaces(line: str) -> str:
    """收敛多余空格：连续空格合并为一个、全角标点前后不留空格、首尾去空白"""
    line = line.replace("\u3000", " ").replace("\xa0", " ")
    line = re.sub(r"[ \t]+", " ", line)
    line = re.sub(r" +(?=" + _FW_PUNCT_RE + ")", "", line)
    line = re.sub(r"(?<=" + _FW_PUNCT_RE + r") +", "", line)
    return line.strip()


def _is_new_entry(line: str) -> bool:
    """判断一行是否为「新的条目」（章节标题/字段标签/项目符号/序号/日期区间开头）"""
    s = line.strip()
    if not s:
        return True
    if is_section(s):
        return True
    if _LABEL_RE.match(s) or _BULLET_RE.match(s) or _NUMBER_RE.match(s) or _DATE_START_RE.match(s):
        return True
    # 含日期区间的行多为「项目/经历」标题（如「XX系统 负责人 2024-01 至 2024-06」）
    if _DATE_RANGE_RE.search(s):
        return True
    return False


def _ends_complete(line: str) -> bool:
    """判断一行是否语义完整（句末标点结尾，或日期/日期区间结尾）"""
    s = line.strip()
    if not s:
        return True
    if s[-1] in _SENT_END:
        return True
    if _DATE_END_RE.search(s) or _DATE_RANGE_RE.search(s):
        return True
    return False


def clean_resume_text(text: str) -> str:
    """清洗简历纯文本：合并被 PDF 视觉换行切断的句子 + 收敛多余空格。

    PDF 提取会把「软换行」（排版折行）当成硬换行，导致句中多出换行；
    这里按「上一行语义未结束且当前行不是新条目」的规则把句子接回去。
    """
    merged: list[str] = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        if merged and not _ends_complete(merged[-1]) and not _is_new_entry(line):
            prev = merged[-1]
            # 两侧都是 ASCII 字母数字时补一个空格，避免把英文单词粘连
            if prev[-1].isascii() and prev[-1].isalnum() and line[0].isascii() and line[0].isalnum():
                merged[-1] = prev + " " + line
            else:
                merged[-1] = prev + line
        else:
            merged.append(line)
    return "\n".join(_normalize_spaces(ln) for ln in merged)


def extract_text(file_bytes: bytes, file_type: str) -> str:
    """根据文件类型提取纯文本"""
    file_type = file_type.lower()
    try:
        if file_type == "pdf":
            return _extract_pdf(file_bytes)
        elif file_type in ("docx", "doc"):
            return _extract_docx(file_bytes)
        else:
            raise BizException(BizCode.FILE_ERROR, f"不支持的文件类型: {file_type}")
    except BizException:
        raise
    except Exception as e:
        raise BizException(BizCode.FILE_ERROR, f"文件解析失败: {str(e)}")


def _extract_pdf(file_bytes: bytes) -> str:
    """pdfplumber 提取 PDF 文本，并合并排版折行"""
    import pdfplumber
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
    return clean_resume_text(normalize_cjk("\n".join(text_parts)))


def _extract_docx(file_bytes: bytes) -> str:
    """python-docx 提取 Word 文本（Word 段落本身可信，仅收敛空格）"""
    import docx
    doc = docx.Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    # 提取表格内容
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                if cell.text.strip():
                    paragraphs.append(cell.text.strip())
    return "\n".join(_normalize_spaces(p) for p in paragraphs if _normalize_spaces(p))
