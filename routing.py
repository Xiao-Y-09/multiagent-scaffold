from langgraph.graph import END

def review_router(state):
    verdict = state.get("verdict", "pass")
    count = state.get("revision_count", 0)
    budget = state.get("max_revisions", 2)
    # 没过 且 预算没用完 → 回去重写;否则(过了 / 预算用完)→ 结束
    if verdict == "revise" and count <= budget:
        return "revise"
    return "pass"

# 路由函数注册表:名字 → 函数(给 config 用名字引用)
ROUTERS = {
    "review_router": review_router,
}