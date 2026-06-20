from tools.retriever import make_retriever

search = make_retriever(k=3)
print(search("你知识库里的某个关键词"))

