# test_stage14.py —— 不用 main.py,直接跑图、看循环转起来
from graph import build_graph

app = build_graph()

init = {
    "topic": "2026 年适合本地跑代码的大模型",   # ← 换成你知识库真正讲到的主题
    "revision_count": 0,
    "max_revisions": 2,                          # 预算:最多重写 2 次
}
config = {"configurable": {"thread_id": "t1"}}

print("===== 逐节点观察 =====")
step = 0
for chunk in app.stream(init, config, stream_mode="updates"):
    for node, delta in chunk.items():
        step += 1
        tail = ""
        if node == "reviewer":
            tail = f"   → verdict={delta.get('verdict')}  revision_count={delta.get('revision_count')}"
        print(f"[{step:>2}] {node}{tail}")

print("\n===== 最终状态 =====")
final = app.get_state(config).values
print("最终 verdict        :", final.get("verdict"))
print("最终 revision_count :", final.get("revision_count"))
print("draft 字数          :", len(final.get("draft", "")))