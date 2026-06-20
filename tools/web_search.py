# tools/web_search.py —— 先占位,接真实 API 时只改这一个函数
def web_search(query: str) -> str:
    return "[搜索结果占位] 关于 " + query + " 的资料……"

# 然后在 researcher 里:先调 web_search,把结果拼进 prompt 再喂模型