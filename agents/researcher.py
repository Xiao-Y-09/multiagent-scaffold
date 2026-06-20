# agents/researcher.py
from langchain_core.messages import SystemMessage, HumanMessage
from tools.retriever import make_retriever

def make_researcher(llm, top_k: int = 4):
    search = make_retriever(k=top_k)   # 工厂里就把检索器建好,闭包里复用

    def researcher(state):
        topic = state["topic"]          # 对齐 state.py:输入字段是 topic ✅
        context = search(topic)         # 真·检索(替换了原来的假 web_search)
        prompt = [
            SystemMessage(content="你是研究助理。只根据【资料】回答,不要编造;资料里没有就说不知道。"),
            HumanMessage(content=f"问题:{topic}\n\n【资料】\n{context}\n\n请整理成要点。"),
        ]
        resp = llm.invoke(prompt)
        return {"research": resp.content}   # 对齐 state.py:输出字段是 research ✅

    return researcher