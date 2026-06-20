# main.py —— 项目收尾:从 config 种入预算,跑完整 RAG + 重写循环,逐轮打印
import yaml
from graph import build_graph

def main():
    app = build_graph()

    # 从 config.yaml 的 settings 读预算
    with open("config.yaml", encoding="utf-8") as f:
        settings = yaml.safe_load(f).get("settings", {})
    max_revisions = settings.get("max_revisions", 2)

    init = {
        "topic": "2026 年适合本地跑代码的大模型",   # ← 换成你知识库真正讲到的主题
        "revision_count": 0,
        "max_revisions": max_revisions,            # 把预算种进 state(router 要用)
    }
    config = {
        "configurable": {"thread_id": "demo-1"},
        "recursion_limit": 50,   # 默认 25;循环会反复跑节点,放开一点更稳妥
    }

    print(f"预算 max_revisions = {max_revisions}\n")
    print("===== 流程逐节点 =====")
    step = 0
    for chunk in app.stream(init, config=config, stream_mode="updates"):
        for node, delta in chunk.items():
            step += 1
            extra = ""
            if node == "reviewer":
                extra = f"  → verdict={delta.get('verdict')}  revision_count={delta.get('revision_count')}"
            print(f"[{step:>2}] {node}{extra}")

    # 流程跑完,从图里取最终累计状态
    final = app.get_state(config).values
    print("\n========== 研究员产出 (research) ==========")
    print(final.get("research"))
    print("\n========== 最终初稿 (draft) ==========")
    print(final.get("draft"))
    print("\n========== 审稿意见 (review) ==========")
    print(final.get("review"))
    print("\n========== 结果 ==========")
    print(f"verdict = {final.get('verdict')}   |   一共重写了 {final.get('revision_count')} 次")

if __name__ == "__main__":
    main()