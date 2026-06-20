from state import State

def make_reviewer(llm):          # llm 从外面传进来
    def reviewer(state: State) -> dict:
        out = llm.invoke([
            ("system", "你是审稿人,对文章进行评价。"),
            ("human", state["draft"]),
        ]).content
        return {"review": out}   # 只返回要写回 State 的字段
    return reviewer
