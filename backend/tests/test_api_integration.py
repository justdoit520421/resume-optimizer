"""
API 全链路集成测试（前端联调前置验证）
生成一份测试简历 DOCX，依次调用后端 5 个接口，验证前后端契约一致。

用法：
  .\\.venv\\Scripts\\python.exe tests\\test_api_integration.py
"""
import io
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import docx

BASE = "http://127.0.0.1:8000/api"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

RESUME_LINES = [
    ("张三", "title"),
    ("电话：138-0000-1234    邮箱：zhangsan@example.com", None),
    ("教育背景", "head"),
    ("2018-2022  某某大学  计算机科学与技术  本科", None),
    ("工作经历", "head"),
    ("2022.07-至今  某互联网科技公司  产品经理", None),
    ("负责用户增长相关工作，推动产品迭代", None),
    ("参与需求分析和产品设计，协调研发团队完成项目上线", None),
    ("项目经历", "head"),
    ("用户增长项目  负责人  2023.03-2023.09", None),
    ("主导用户增长策略，提升日活；优化注册流程", None),
    ("技能", "head"),
    ("产品规划、数据分析、用户研究、Axure、Figma", None),
    ("自我评价", "head"),
    ("5年产品经验，擅长用户增长，具备良好的沟通协调能力。", None),
]

JD_TEXT = """岗位：高级产品经理（用户增长方向）
职责：负责用户增长策略制定与执行，提升 DAU、留存率；通过数据分析驱动产品决策，设计 A/B 实验。
要求：3年以上互联网产品经验；熟悉数据分析，能独立完成数据看板搭建；具备 SQL 能力；有商业化经验优先。"""


def build_docx() -> bytes:
    document = docx.Document()
    for text, style in RESUME_LINES:
        if style == "title":
            document.add_heading(text, level=0)
        elif style == "head":
            document.add_heading(text, level=1)
        else:
            document.add_paragraph(text)
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


def show(title, data, limit=700):
    print(f"\n--- {title} ---")
    print(json.dumps(data, ensure_ascii=False, indent=2)[:limit])


def main():
    results = []

    # 1. 上传
    print("=" * 60)
    print("步骤 1：上传简历")
    print("=" * 60)
    files = {"file": ("test_resume.docx", build_docx(), DOCX_MIME)}
    r = httpx.post(f"{BASE}/resumes/upload", files=files, timeout=60)
    body = r.json()
    show("upload 响应", body)
    if body.get("code") != 0:
        print("[FAIL] 上传失败")
        return 1
    resume_id = body["data"]["resume_id"]
    print(f"[PASS] resume_id = {resume_id}")
    results.append(True)

    # 2. 解析
    print("\n" + "=" * 60)
    print("步骤 2：解析简历（调用 DeepSeek）")
    print("=" * 60)
    r = httpx.post(f"{BASE}/resumes/{resume_id}/parse", timeout=180)
    body = r.json()
    parsed = body.get("data", {}).get("parsed", {})
    show("parse 响应", {"resume_id": body.get("data", {}).get("resume_id"), "parsed": parsed})
    ok = bool(body.get("code") == 0 and parsed.get("work_experience"))
    results.append(ok)
    print("[PASS] 解析成功" if ok else "[FAIL] 解析失败")

    # 3. 评分
    print("\n" + "=" * 60)
    print("步骤 3：智能评分")
    print("=" * 60)
    r = httpx.post(f"{BASE}/resumes/{resume_id}/score", params={"target_job": "产品经理"}, timeout=180)
    body = r.json()
    show("score 响应", body.get("data"))
    dims = body.get("data", {}).get("dimensions", [])
    ok = body.get("code") == 0 and len(dims) == 6
    results.append(ok)
    print(f"[PASS] 评分成功，共 {len(dims)} 个维度" if ok else "[FAIL] 评分失败")

    # 4. 优化
    print("\n" + "=" * 60)
    print("步骤 4：一键优化（产品岗）")
    print("=" * 60)
    r = httpx.post(f"{BASE}/resumes/{resume_id}/optimize", json={"job_type": "product"}, timeout=180)
    body = r.json()
    sug = body.get("data", {}).get("suggestions", [])
    show("optimize 响应", {"count": len(sug), "first": sug[0] if sug else None})
    ok = body.get("code") == 0 and len(sug) > 0
    results.append(ok)
    print(f"[PASS] 优化成功，共 {len(sug)} 条建议" if ok else "[FAIL] 优化失败")

    # 5. 应用建议（前端"接受"动作）
    if sug:
        print("\n" + "=" * 60)
        print("步骤 5：应用建议（模拟前端逐条接受）")
        print("=" * 60)
        r = httpx.post(f"{BASE}/resumes/{resume_id}/apply-suggestions",
                       json={"accepted_indices": list(range(min(2, len(sug))))}, timeout=60)
        body = r.json()
        ok = body.get("code") == 0 and body["data"]["accepted_count"] > 0
        show("apply 响应", {"accepted_count": body.get("data", {}).get("accepted_count"),
                            "optimized_len": len(body.get("data", {}).get("optimized_text", ""))})
        results.append(ok)
        print("[PASS] 应用建议成功" if ok else "[FAIL] 应用建议失败")

    # 6. 岗位匹配
    print("\n" + "=" * 60)
    print("步骤 6：岗位匹配")
    print("=" * 60)
    r = httpx.post(f"{BASE}/resumes/{resume_id}/match", json={"jd_text": JD_TEXT}, timeout=180)
    body = r.json()
    show("match 响应", body.get("data"))
    ok = body.get("code") == 0 and isinstance(body.get("data", {}).get("match_score"), int)
    results.append(ok)
    print("[PASS] 匹配成功" if ok else "[FAIL] 匹配失败")

    print("\n" + "=" * 60)
    print(f"集成测试结果: {sum(results)}/{len(results)} 通过")
    print("=" * 60)
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
