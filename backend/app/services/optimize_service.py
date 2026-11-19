# 一键优化服务
from app.services.llm_service import get_llm
from app.prompts import build_optimize_system


def optimize_resume(raw_text: str, job_type: str = "product") -> dict:
    """按岗位类型生成逐条优化建议"""
    llm = get_llm()
    system_prompt = build_optimize_system(job_type)
    result = llm.structured_chat(system_prompt, f"简历原文：\n{raw_text}")
    # 为每条建议补充 accepted=False
    items = result.get("items", [])
    for item in items:
        item.setdefault("accepted", False)
    return {"items": items}
