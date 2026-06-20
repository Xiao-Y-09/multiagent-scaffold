from typing import TypedDict

class State(TypedDict, total=False):
    topic: str
    research: str
    draft: str
    review: str
    verdict: str          # "pass" / "revise"
    revision_count: int   # reviewer 已累计判 revise 的次数
    max_revisions: int    # 预算(由 main 从 config 读入种进来)