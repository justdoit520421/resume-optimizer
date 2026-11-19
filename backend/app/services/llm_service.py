# LLM 适配层：统一调用接口，支持 mock / openai / qwen / ernie
import json
from abc import ABC, abstractmethod

from app.config import settings
from app.exceptions import BizException
from app.response import BizCode


class BaseLLM(ABC):
    """LLM 抽象基类"""

    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """返回模型原始文本"""
        ...

    def structured_chat(self, system_prompt: str, user_prompt: str, retries: int = 1) -> dict:
        """调用并解析 JSON 输出；失败自动重试，重试仍失败才抛错"""
        import logging
        logger = logging.getLogger("llm")

        last_raw = ""
        for attempt in range(retries + 1):
            raw = self.chat(system_prompt, user_prompt) or ""
            parsed = self._try_parse(raw)
            if parsed is not None:
                return parsed
            last_raw = raw
            logger.warning(
                "LLM JSON 解析失败 (attempt %d/%d)，返回片段: %.200s",
                attempt + 1, retries + 1, raw or "<空>",
            )
        raise BizException(
            BizCode.LLM_ERROR,
            "大模型返回内容无法解析为 JSON（自动重试后仍失败），请稍后再试",
        )

    @staticmethod
    def _try_parse(raw: str):
        """多级容错解析：直接解析 -> ```json 代码块 -> 首尾大括号片段"""
        if not raw or not raw.strip():
            return None
        # 1) 直接解析
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
        # 2) 提取 ```json ... ``` 代码块
        fenced = None
        if "```json" in raw:
            fenced = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            fenced = raw.split("```")[1].split("```")[0]
        if fenced:
            try:
                return json.loads(fenced.strip())
            except json.JSONDecodeError:
                pass
        # 3) 截取首个 { 到最后一个 } 的片段（剥离 JSON 前后的杂质文字）
        start, end = raw.find("{"), raw.rfind("}")
        if 0 <= start < end:
            try:
                return json.loads(raw[start:end + 1])
            except json.JSONDecodeError:
                pass
        return None


class MockLLM(BaseLLM):
    """Mock 实现：无 API Key 时本地演示，返回预设数据"""

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        # 根据 user_prompt 关键词返回不同的 mock 数据
        if "解析" in system_prompt or "parse" in system_prompt.lower():
            return json.dumps({
                "basic_info": {"name": "张三", "phone": "138****8888", "email": "zhangsan@example.com"},
                "education": [{"school": "某某大学", "major": "计算机科学", "degree": "本科", "period": "2018-2022"}],
                "work_experience": [
                    {"company": "某科技公司", "position": "产品经理", "period": "2022-至今",
                     "content": "负责用户增长相关工作，推动产品迭代"}
                ],
                "projects": [
                    {"name": "用户增长项目", "role": "负责人", "period": "2023",
                     "content": "主导用户增长策略，提升日活"}
                ],
                "skills": ["产品规划", "数据分析", "用户研究"],
                "self_evaluation": "5年产品经验，擅长用户增长"
            }, ensure_ascii=False)

        if "评分" in system_prompt or "score" in system_prompt.lower():
            return json.dumps({
                "dimensions": [
                    {"name": "完整性", "score": 12, "max_score": 15, "reason": "信息基本齐全"},
                    {"name": "量化程度", "score": 10, "max_score": 25, "reason": "经历中缺乏数据支撑"},
                    {"name": "关键词匹配", "score": 18, "max_score": 25, "reason": "与目标岗位关键词重合度中等"},
                    {"name": "逻辑结构", "score": 11, "max_score": 15, "reason": "条理较清晰"},
                    {"name": "表达质量", "score": 7, "max_score": 10, "reason": "语言简洁但专业度一般"},
                    {"name": "岗位契合度", "score": 7, "max_score": 10, "reason": "经历与岗位方向匹配"}
                ],
                "total": 65,
                "summary": "简历结构完整，但缺乏量化成果，建议补充具体数据。"
            }, ensure_ascii=False)

        if "优化" in system_prompt or "optimize" in system_prompt.lower():
            return json.dumps({
                "items": [
                    {"original": "负责用户增长相关工作",
                     "improved": "主导用户增长项目，通过搭建裂变体系与投放优化，3个月内 DAU 从 5w 提升至 12w",
                     "reason": "补充具体动作 + 量化成果，遵循 STAR 法则", "type": "quantification"},
                    {"original": "推动产品迭代",
                     "improved": "主导 3 个核心版本迭代，优化核心转化率 25%",
                     "reason": "量化迭代成果，突出业务价值", "type": "quantification"}
                ]
            }, ensure_ascii=False)

        if "匹配" in system_prompt or "match" in system_prompt.lower():
            return json.dumps({
                "match_score": 72,
                "matched": ["产品规划", "数据分析", "用户增长经验"],
                "missing": ["A/B 测试经验", "SQL 数据查询", "商业化变现经验"],
                "suggestions": [
                    "补充 A/B 测试相关项目经历",
                    "在技能中加入 SQL / 数据可视化工具",
                    "增加商业化或营收相关成果描述"
                ]
            }, ensure_ascii=False)

        return json.dumps({"result": "mock default"})


# 各厂商默认配置（base_url 与默认模型），均为 OpenAI 兼容接口
PROVIDER_CONFIG = {
    "openai":   {"base_url": None,                       "model": "gpt-4o-mini"},
    "deepseek": {"base_url": "https://api.deepseek.com", "model": "deepseek-chat"},
    "qwen":     {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "glm":      {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    "kimi":     {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "doubao":   {"base_url": "https://ark.cn-beijing.volces.com/api/v3", "model": "doubao-pro-32k"},
    "ernie":    {"base_url": "https://qianfan.baidubce.com/v2", "model": "ernie-4.0-turbo-8k"},
}


class OpenAILLM(BaseLLM):
    """OpenAI 兼容接口：覆盖 OpenAI / DeepSeek / 通义 / 智谱 / Kimi / 豆包 / 文心"""

    def __init__(self):
        from openai import OpenAI
        provider = settings.LLM_PROVIDER.lower()
        cfg = PROVIDER_CONFIG.get(provider, PROVIDER_CONFIG["openai"])
        # 用户显式配置的 base_url / model 优先级最高
        base_url = settings.LLM_BASE_URL or cfg["base_url"]
        model = settings.LLM_MODEL or cfg["model"]
        if not settings.LLM_API_KEY:
            raise BizException(BizCode.LLM_ERROR, f"LLM_PROVIDER={provider} 需要配置 LLM_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=settings.LLM_API_KEY, base_url=base_url)

    def chat(self, system_prompt: str, user_prompt: str) -> str:
        try:
            kwargs = {}
            if settings.LLM_MAX_TOKENS > 0:
                kwargs["max_tokens"] = settings.LLM_MAX_TOKENS
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},  # 强制 JSON 输出（OpenAI 兼容）
                **kwargs,
            )
            choice = resp.choices[0]
            if choice.finish_reason == "length":
                # 输出被截断，JSON 必然不完整，直接给出明确错误
                raise BizException(
                    BizCode.LLM_ERROR,
                    "大模型输出因 max_tokens 上限被截断，请精简简历内容或调大 LLM_MAX_TOKENS",
                )
            return choice.message.content
        except BizException:
            raise
        except Exception as e:
            raise BizException(BizCode.LLM_ERROR, f"大模型调用失败: {str(e)}")


def get_llm() -> BaseLLM:
    """工厂方法：根据配置返回对应 LLM 实例"""
    provider = settings.LLM_PROVIDER.lower()
    if provider == "mock":
        return MockLLM()
    return OpenAILLM()
