# 简历解析服务：文本提取 + LLM 结构化
from app.services.extract_service import extract_text
from app.services.llm_service import get_llm
from app.prompts import RESUME_PARSE_SYSTEM


def parse_resume(file_bytes: bytes, file_type: str) -> dict:
    """提取文本并通过 LLM 结构化"""
    raw_text = extract_text(file_bytes, file_type)
    llm = get_llm()
    parsed = llm.structured_chat(RESUME_PARSE_SYSTEM, f"简历原文：\n{raw_text}")
    return {"raw_text": raw_text, "parsed": parsed}
