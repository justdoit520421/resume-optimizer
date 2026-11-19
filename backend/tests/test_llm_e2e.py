"""
真实 LLM 端到端测试脚本
验证 4 个核心 Prompt（解析/评分/优化/匹配）的输出质量

用法：
  1. 设置环境变量或在 backend/.env 中配置：
     LLM_PROVIDER=deepseek   # 可选 openai/deepseek/qwen/glm/kimi/doubao/ernie
     LLM_API_KEY=sk-xxx
  2. 运行： .\\.venv\\Scripts\\python.exe tests\\test_llm_e2e.py

无 API Key 时自动跳过并给出配置指引。
"""
import json
import sys
import os

# 确保能 import app 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.llm_service import get_llm
from app.prompts import RESUME_PARSE_SYSTEM, SCORE_SYSTEM, build_optimize_system, MATCH_SYSTEM


# 测试用简历样本（模拟一份中等质量的产品经理简历）
SAMPLE_RESUME = """
张三
电话：138-0000-1234  邮箱：zhangsan@example.com

教育背景
2018-2022 某某大学 计算机科学与技术 本科

工作经历
2022.07-至今  某互联网科技公司  产品经理
- 负责用户增长相关工作，推动产品迭代
- 参与需求分析和产品设计
- 协调研发团队完成项目上线

项目经历
用户增长项目  负责人  2023.03-2023.09
- 主导用户增长策略，提升日活
- 优化注册流程

技能
产品规划、数据分析、用户研究、Axure、Figma

自我评价
5年产品经验，擅长用户增长，具备良好的沟通协调能力。
"""

SAMPLE_JD = """
岗位：高级产品经理（用户增长方向）
职责：
- 负责用户增长策略制定与执行，提升 DAU、留存率
- 通过数据分析驱动产品决策，设计 A/B 实验
- 主导核心功能的产品设计与迭代
要求：
- 3年以上互联网产品经验，有用户增长经验优先
- 熟悉数据分析，能独立完成数据看板搭建
- 具备 SQL 能力，熟悉常用数据工具
- 有商业化或营收相关经验优先
"""


def assert_structured(label: str, data: dict, required_keys: list, key_types: dict = None):
    """结构性断言：检查必需字段与类型（容忍 LLM 输出的非确定性）"""
    ok = True
    for k in required_keys:
        if k not in data:
            print(f"  [FAIL] {label}: 缺少字段 '{k}'")
            ok = False
    if key_types:
        for k, t in key_types.items():
            if k in data and not isinstance(data[k], t):
                print(f"  [FAIL] {label}: 字段 '{k}' 类型应为 {t.__name__}，实际 {type(data[k]).__name__}")
                ok = False
    if ok:
        print(f"  [PASS] {label}: 结构校验通过")
    return ok


def test_parse(llm):
    print("\n" + "=" * 60)
    print("测试 1：简历结构化解析")
    print("=" * 60)
    result = llm.structured_chat(RESUME_PARSE_SYSTEM, f"简历原文：\n{SAMPLE_RESUME}")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:800])
    return assert_structured("解析", result,
                             required_keys=["basic_info", "education", "work_experience", "skills"],
                             key_types={"education": list, "work_experience": list, "skills": list})


def test_score(llm):
    print("\n" + "=" * 60)
    print("测试 2：智能评分")
    print("=" * 60)
    result = llm.structured_chat(SCORE_SYSTEM, f"目标岗位：产品经理\n\n简历原文：\n{SAMPLE_RESUME}")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:800])
    ok = assert_structured("评分", result,
                           required_keys=["dimensions", "total", "summary"],
                           key_types={"dimensions": list, "total": int, "summary": str})
    # 校验维度数量与总分范围
    if ok and len(result.get("dimensions", [])) == 6:
        print("  [PASS] 评分: 6 个维度齐全")
    else:
        print(f"  [WARN] 评分: 维度数量={len(result.get('dimensions', []))}（期望 6）")
        ok = False
    if ok and 0 <= result.get("total", -1) <= 100:
        print("  [PASS] 评分: 总分在 0-100 范围内")
    else:
        ok = False
    return ok


def test_optimize(llm):
    print("\n" + "=" * 60)
    print("测试 3：一键优化（产品岗）")
    print("=" * 60)
    system = build_optimize_system("product")
    result = llm.structured_chat(system, f"简历原文：\n{SAMPLE_RESUME}")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:1000])
    ok = assert_structured("优化", result, required_keys=["items"], key_types={"items": list})
    items = result.get("items", [])
    if ok and items:
        # 校验每条建议的字段
        first = items[0]
        ok = assert_structured("优化条目", first,
                               required_keys=["original", "improved", "reason", "type"],
                               key_types={"original": str, "improved": str, "reason": str, "type": str})
        valid_types = {"quantification", "wording", "structure", "keyword"}
        if first.get("type") not in valid_types:
            print(f"  [WARN] 优化: type='{first.get('type')}' 不在预定义集合中")
    return ok


def test_match(llm):
    print("\n" + "=" * 60)
    print("测试 4：岗位匹配")
    print("=" * 60)
    result = llm.structured_chat(MATCH_SYSTEM, f"岗位描述（JD）：\n{SAMPLE_JD}\n\n简历原文：\n{SAMPLE_RESUME}")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:800])
    ok = assert_structured("匹配", result,
                           required_keys=["match_score", "matched", "missing", "suggestions"],
                           key_types={"matched": list, "missing": list, "suggestions": list})
    if ok and 0 <= result.get("match_score", -1) <= 100:
        print("  [PASS] 匹配: match_score 在 0-100 范围内")
    else:
        ok = False
    return ok


def main():
    provider = settings.LLM_PROVIDER.lower()
    print(f"当前 LLM 配置: provider={provider}, model={settings.LLM_MODEL or '(厂商默认)'}")

    if provider == "mock" or not settings.LLM_API_KEY:
        print("\n[跳过] 未配置真实 LLM API Key，无法进行真实调用测试。")
        print("配置方法：")
        print("  方式一：在 backend/.env 中设置")
        print("    LLM_PROVIDER=deepseek")
        print("    LLM_API_KEY=sk-你的key")
        print("  方式二：设置环境变量")
        print("    $env:LLM_PROVIDER='deepseek'")
        print("    $env:LLM_API_KEY='sk-你的key'")
        print("\n支持的厂商：openai / deepseek / qwen / glm / kimi / doubao / ernie")
        print("（DeepSeek 新用户有免费额度，适合快速测试）")
        return 1

    try:
        llm = get_llm()
    except Exception as e:
        print(f"[错误] LLM 初始化失败: {e}")
        return 1

    results = []
    results.append(test_parse(llm))
    results.append(test_score(llm))
    results.append(test_optimize(llm))
    results.append(test_match(llm))

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"测试结果: {passed}/{total} 通过")
    if passed == total:
        print("全部通过！Prompt 输出结构符合预期。")
    else:
        print(f"{total - passed} 项未通过，建议检查 Prompt 或模型对 JSON 输出的支持。")
    print("=" * 60)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
