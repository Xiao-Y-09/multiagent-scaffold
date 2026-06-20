from vectorstore import get_vectorstore

def make_retriever(k: int = 4):
    vs = get_vectorstore()
    retriever = vs.as_retriever(search_kwargs={"k": k})

    def search(query: str) -> str:
        docs = retriever.invoke(query)
        if not docs:
            return "(知识库里没查到相关内容)"
        blocks = []
        for i, d in enumerate(docs, 1):
            src = d.metadata.get("source", "?")
            blocks.append(f"[{i}] 来源: {src}\n{d.page_content}")
        return "\n\n".join(blocks)

    return search