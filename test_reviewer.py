# test_reviewer.py —— 验 reviewer 接真模型时能吐出 pass/revise 并被正确解析
from langchain_ollama import ChatOllama
from agents.reviewer import make_reviewer

# 4b 跑得快、省显存;想判得更准可换 gemma3:27b。temperature=0 让它更老实地只吐 JSON
llm = ChatOllama(model="gemma3:4b", base_url="http://127.0.0.1:11434", temperature=0)
reviewer = make_reviewer(llm)

bad_draft = "AI 很好。AI 很厉害。它能做很多事。完。"   # 故意写得很烂,看它怎么判
out = reviewer({"draft": bad_draft})

print("verdict        :", out["verdict"])          # 应该是干净的 'pass' 或 'revise'(不是一整段 JSON)
print("revision_count :", out["revision_count"])   # revise → 1;pass → 0
print("review(comment):", out["review"][:200])