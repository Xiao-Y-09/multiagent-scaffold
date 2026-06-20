# test_router.py —— 只测路由逻辑,不连 LLM,瞬间出结果
from routing import review_router

def case(state, expect):
    got = review_router(state)
    flag = "OK  " if got == expect else "FAIL"
    print(f"[{flag}] {state} -> {got}  (期望 {expect})")

# ⚠️ 下面字典的 key 要和你 review_router 里 state.get(...) 读的名字一致!
#    如果你的计数器叫 revisions 而不是 revision_count,把下面三行的 revision_count 全改成 revisions。
case({"verdict": "revise", "revision_count": 1, "max_revisions": 2}, "revise")  # 要改 且 没超预算 → 打回 writer
case({"verdict": "revise", "revision_count": 3, "max_revisions": 2}, "pass")    # 要改 但 超预算 → 强制结束(刹车)
case({"verdict": "pass",   "revision_count": 0, "max_revisions": 2}, "pass")    # 通过 → 结束