import yaml
from langgraph.graph import StateGraph, START, END
from state import State
from llm_factory import make_llm
from registry import AGENT_FACTORIES

cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
builder = StateGraph(State)

# 1) 建节点:按配置给每个 agent 造好模型,再注入
for name, make in AGENT_FACTORIES.items():
    llm = make_llm(cfg["agents"][name]["model"])
    builder.add_node(name, make(llm))

# 2) 按 config 连边(和阶段 4 一样)
builder.add_edge(START, cfg["entry"])
for src, dst in cfg["edges"].items():
    builder.add_edge(src, END if dst == "END" else dst)

# graph.py
from langgraph.checkpoint.memory import MemorySaver
graph = builder.compile(checkpointer=MemorySaver())