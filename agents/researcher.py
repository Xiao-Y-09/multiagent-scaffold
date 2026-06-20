from state import State

def make_researcher(llm):          # llm 从外面传进来
    def researcher(state: State) -> dict:
        out = llm.invoke([
            ("system", "你是研究员,只列要点。"),
            ("human", state["topic"]),
        ]).content
        return {"research": out}
    return researcher