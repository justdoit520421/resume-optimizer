# 岗位匹配服务
from app.services.llm_service import get_llm
from app.prompts import MATCH_SYSTEM


def match_job(raw_text: str, jd_text: str) -> dict:
    """分析简历与 JD 的匹配度与差距"""
    llm = get_llm()
    user_prompt = f"岗位描述（JD）：\n{jd_text}\n\n简历原文：\n{raw_text}"
    result = llm.structured_chat(MATCH_SYSTEM, user_prompt)
    return result
