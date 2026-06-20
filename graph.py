import yaml
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from state import State
from registry import AGENT_FACTORIES
from routing import ROUTERS
from llm_factory import make_llm

def build_graph(config_path: str = "config.yaml"):
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    g = StateGraph(State)

    # 1) 加节点:把 model 以外的字段(如 top_k)透传给工厂
    for name, acfg in cfg["agents"].items():
        llm = make_llm(acfg)
        factory = AGENT_FACTORIES[name]
        kwargs = {k: v for k, v in acfg.items() if k != "model"}
        g.add_node(name, factory(llm, **kwargs))

    # 2) 入口
    g.add_edge(START, cfg["entry"])

    # 3) 普通边
    for src, dst in cfg.get("edges", []):
        g.add_edge(src, dst)

    # 4) 条件边
    for ce in cfg.get("conditional_edges", []):
        router = ROUTERS[ce["router"]]
        path_map = {
            label: (END if target == "END" else target)
            for label, target in ce["paths"].items()
        }
        g.add_conditional_edges(ce["source"], router, path_map)

    return g.compile(checkpointer=MemorySaver())