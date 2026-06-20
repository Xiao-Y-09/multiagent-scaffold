'''
'''

from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gemma3:4b",                    # 先用小模型,3 个 agent 跑得快
    base_url="http://127.0.0.1:11434",   # Windows 必加:绕开 localhost→IPv6
)

def agent(system, user):
    # 一个 agent = 一次带「角色设定」的模型调用
    msg = llm.invoke([("system", system), ("human", user)]) # .invoke([("system", system), ("human", user)]), 
    # 而不是 .invoke(user), 因为要带上 system 角色设定, input: [("system", system), ("human", user)]
    return msg.content

# 三个角色不同的 agent:前一个的输出当后一个的输入
research = agent("你是研究员,只列要点。", "调研 RAG 的核心思想")
draft    = agent("你是写作者,根据要点写一段初稿。", research)
review   = agent("你是审稿人,挑出问题并给出改进版。", draft)

print(review)