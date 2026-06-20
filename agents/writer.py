from langchain_core.messages import SystemMessage, HumanMessage

def make_writer(llm):
    def writer(state):
        research = state.get("research", "")
        feedback = state.get("review", "")   # 第一轮为空;重写时有审稿意见
        extra = f"\n\n审稿意见(请据此修改):\n{feedback}" if feedback else ""
        prompt = [
            SystemMessage(content="你是写作者,根据资料写一篇结构清晰的短文。"),
            HumanMessage(content=f"资料:\n{research}{extra}\n\n请输出正文。"),
        ]
        resp = llm.invoke(prompt)
        return {"draft": resp.content}
    return writer