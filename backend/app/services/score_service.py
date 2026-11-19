# 智能评分服务
from app.services.llm_service import get_llm
from app.prompts import SCORE_SYSTEM


def score_resume(raw_text: str, target_job: str = "") -> dict:
    """调用 LLM 对简历进行多维度评分"""
    llm = get_llm()
    user_prompt = f"目标岗位：{target_job or '通用'}\n\n简历原文：\n{raw_text}"
    result = llm.structured_chat(SCORE_SYSTEM, user_prompt)
    return result
