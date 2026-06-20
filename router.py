def route_after_review(state) -> str:
    approved = "通过" in state["review"]
    revisions = state.get("revisions", 0)
    decision = "end" if (approved or revisions >= 2) else "rewrite"
    print(f"[路由] 第 {revisions} 稿,审稿{'通过' if approved else '未通过'} → {decision}")
    return decision