from langchain_ollama import ChatOllama

def make_llm(model_cfg: dict):
    provider = model_cfg.get("provider", "ollama")
    if provider == "ollama":
        return ChatOllama(
            model=model_cfg["model"],
            base_url="http://127.0.0.1:11434",   # ← Windows 必加,大概率你漏了这行
            num_ctx=8192,
        )
    raise ValueError("未知 provider: " + provider)