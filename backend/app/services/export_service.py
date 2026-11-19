# 简历导出服务：将优化后文本导出为 Word / PDF
# 版式约定：正文宋体、标题黑体；章节标题加粗并带下分隔线；紧凑排版尽量一页
import io
import os
from xml.sax.saxutils import escape

from app.exceptions import BizException
from app.response import BizCode
from app.services.extract_service import is_section

# 正文字体：宋体；标题字体：黑体
_BODY_FONT_EA = "宋体"
_HEAD_FONT_EA = "黑体"
_BODY_FONT_ASCII = "Times New Roman"
_HEAD_FONT_ASCII = "Arial"


def _classify_lines(text: str):
    """把纯文本拆成行，并标记每行类型：title（首行）/ section（章节标题）/ body"""
    lines = [ln.strip() for ln in text.replace("\r\n", "\n").split("\n")]
    lines = [ln for ln in lines if ln]
    result = []
    for i, ln in enumerate(lines):
        if i == 0:
            result.append(("title", ln))
        elif is_section(ln):
            result.append(("section", ln.rstrip("：: ")))
        else:
            result.append(("body", ln))
    return result


# ---------------- Word ----------------

def _set_run_font(run, ea_font: str, ascii_font: str, size_pt: float, bold: bool):
    """同时设置中文字体（eastAsia）与西文字体"""
    from docx.shared import Pt
    run.font.name = ascii_font
    run.font.size = Pt(size_pt)
    run.bold = bold
    run.element.rPr.rFonts.set(
        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}eastAsia",
        ea_font,
    )


def build_docx(text: str) -> bytes:
    """生成 Word（.docx）字节流"""
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    doc = Document()
    # 窄页边距，压缩到一页
    for section in doc.sections:
        section.top_margin = Cm(1.5)
        section.bottom_margin = Cm(1.5)
        section.left_margin = Cm(1.8)
        section.right_margin = Cm(1.8)

    for kind, ln in _classify_lines(text):
        p = doc.add_paragraph()
        pf = p.paragraph_format
        if kind == "title":
            run = p.add_run(ln)
            _set_run_font(run, _HEAD_FONT_EA, _HEAD_FONT_ASCII, 16, True)
            pf.space_after = Pt(4)
        elif kind == "section":
            run = p.add_run(ln)
            _set_run_font(run, _HEAD_FONT_EA, _HEAD_FONT_ASCII, 11.5, True)
            pf.space_before = Pt(6)
            pf.space_after = Pt(2)
            # 标题下方加横线（参考简历版式）
            pPr = p._p.get_or_add_pPr()
            pBdr = OxmlElement("w:pBdr")
            bottom = OxmlElement("w:bottom")
            bottom.set(qn("w:val"), "single")
            bottom.set(qn("w:sz"), "8")
            bottom.set(qn("w:color"), "333333")
            pBdr.append(bottom)
            pPr.append(pBdr)
        else:
            run = p.add_run(ln)
            _set_run_font(run, _BODY_FONT_EA, _BODY_FONT_ASCII, 10.5, False)
            pf.space_after = Pt(1)
            pf.line_spacing = 1.12

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ---------------- PDF ----------------

def _register_pdf_fonts():
    """注册正文字体（宋体）与标题字体（黑体），返回 (body_font, head_font)"""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    def _try(name, path, idx=None):
        if not os.path.exists(path):
            return False
        try:
            if idx is not None:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=idx))
            else:
                pdfmetrics.registerFont(TTFont(name, path))
            return True
        except Exception:
            return False

    body = head = None
    # 宋体（正文）
    for args in [("C:/Windows/Fonts/simsun.ttc", 0), ("C:/Windows/Fonts/SimSun.ttf", None)]:
        if _try("SimSun", *args):
            body = "SimSun"
            break
    # 黑体（标题）
    for args in [("C:/Windows/Fonts/simhei.ttf", None), ("C:/Windows/Fonts/msyh.ttc", 0)]:
        if _try("SimHei", *args):
            head = "SimHei"
            break
    # 兜底：内置 CID 字体
    if not body or not head:
        from reportlab.pdfbase.cidfonts import UnicodeCIDFont
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        body = body or "STSong-Light"
        head = head or "STSong-Light"
    return body, head


def build_pdf(text: str) -> bytes:
    """生成 PDF 字节流"""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    )

    body_font, head_font = _register_pdf_fonts()

    styles = {
        "title": ParagraphStyle(
            "title", fontName=head_font, fontSize=16, leading=20, spaceAfter=4,
        ),
        "section": ParagraphStyle(
            "section", fontName=head_font, fontSize=11.5, leading=15,
            spaceBefore=5, spaceAfter=2,
        ),
        "body": ParagraphStyle(
            "body", fontName=body_font, fontSize=10, leading=14,
        ),
    }

    story = []
    for kind, ln in _classify_lines(text):
        story.append(Paragraph(escape(ln), styles[kind]))
        if kind == "section":
            # 章节标题下方横线
            story.append(HRFlowable(width="100%", thickness=0.8, color="#333333"))
        elif kind == "body":
            story.append(Spacer(1, 0.6 * mm))

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
    )
    doc.build(story)
    return buf.getvalue()


def _clean_text(text: str) -> str:
    """导出前清洗：剔除控制字符、归一化部首码位、合并排版折行并收敛空格"""
    from app.services.extract_service import normalize_cjk, clean_resume_text

    text = "".join(
        ch for ch in normalize_cjk(text)
        if ch in "\n\t" or (ord(ch) >= 0x20 and ord(ch) != 0x7F)
    )
    return clean_resume_text(text)


def export_resume(text: str, fmt: str) -> bytes:
    """按格式导出，fmt: docx / pdf"""
    if not text or not text.strip():
        raise BizException(BizCode.NOT_FOUND, "暂无可导出的优化后内容，请先应用优化建议")
    text = _clean_text(text)
    if fmt == "docx":
        return build_docx(text)
    if fmt == "pdf":
        return build_pdf(text)
    raise BizException(BizCode.PARAM_ERROR, "不支持的导出格式，仅支持 docx / pdf")
