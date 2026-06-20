from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="gemma3:27b",
    base_url="http://127.0.0.1:11434",   # 明确用 IPv4,绕开 localhost→IPv6 的坑
)
print(llm.invoke("用一句话介绍你自己").content)