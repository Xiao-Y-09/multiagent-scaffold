from typing import TypedDict

class State(TypedDict):
    topic: str       # 输入:主题
    research: str    # 研究员产出
    draft: str       # 写作产出
    review: str      # 审稿产出
    revisions: int   # 已重写次数