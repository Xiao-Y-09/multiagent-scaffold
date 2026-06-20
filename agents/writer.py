from state import State

def make_writer(llm):          # llm 从外面传进来
    def writer(state: State) -> dict:
        out = llm.invoke([
            ("system", "你是作家,根据研究员的要点撰写文章。"),
            ("human", state["research"]),
        ]).content
        return {"draft": out, "revisions": state.get("revisions", 0) + 1}
    return writer