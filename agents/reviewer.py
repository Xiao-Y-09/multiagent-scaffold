import json, re
from langchain_core.messages import SystemMessage, HumanMessage

def make_reviewer(llm):
    def reviewer(state):
        draft = state["draft"]
        prompt = [
            SystemMessage(content=(
                "你是审稿人,判断草稿是否合格。"
                '只输出 JSON,不要别的:{"verdict": "pass" 或 "revise", "comment": "原因/修改建议"}'
            )),
            HumanMessage(content=f"草稿:\n{draft}"),
        ]
        resp = llm.invoke(prompt)
        verdict, comment = _parse(resp.content)
        count = state.get("revision_count", 0) + (1 if verdict == "revise" else 0)
        return {"review": comment, "verdict": verdict, "revision_count": count}
    return reviewer

def _parse(text: str):
    """LLM 不一定老实只吐 JSON,做防呆解析。"""
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            v = str(obj.get("verdict", "pass")).lower()
            return ("revise" if v == "revise" else "pass"), obj.get("comment", "")
        except Exception:
            pass
    return ("revise" if "revise" in text.lower() else "pass"), text.strip()