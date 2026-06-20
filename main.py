from graph import graph

config = {"configurable": {"thread_id": "session-1"}}
result = graph.invoke({"topic": "RAG 的核心思想"}, config=config)

print("\n========== 研究员产出 ==========")
print(result["research"])

print("\n========== 最终初稿 (draft) ==========")
print(result["draft"])

print("\n========== 审稿意见 (review) ==========")
print(result["review"])

print(f"\n========== 一共重写了 {result.get('revisions', 0)} 次 ==========")