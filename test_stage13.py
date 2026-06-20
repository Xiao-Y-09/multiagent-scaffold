# test_stage13.py —— 阶段 13 的纯逻辑测试(不连 LLM,瞬间出结果)
from routing import review_router
from agents.reviewer import _parse

print("===== 路由逻辑 review_router =====")
def case(state, expect):
    got = review_router(state)
    flag = "OK  " if got == expect else "FAIL"
    print(f"[{flag}] {state} -> {got}  (期望 {expect})")

case({"verdict": "revise", "revision_count": 1, "max_revisions": 2}, "revise")  # 要改 且 没超预算 → 打回 writer
case({"verdict": "revise", "revision_count": 3, "max_revisions": 2}, "pass")    # 要改 但 超预算 → 刹车结束(防死循环)
case({"verdict": "pass",   "revision_count": 0, "max_revisions": 2}, "pass")    # 通过 → 结束

print("\n===== 防呆解析 _parse =====")
samples = [
    '前面扯两句 {"verdict": "revise", "comment": "太短了"} 后面再扯',  # JSON 混在文字里 → 要能抠出来
    '我觉得需要 revise 一下,理由是……',                               # 没 JSON,但有 revise 关键词 → 兜底
    '这篇写得不错',                                                     # 啥信号都没有 → 默认 pass
]
for s in samples:
    print(_parse(s), "  <-", s[:30])