from agents.researcher import make_researcher
from agents.writer import make_writer
from agents.reviewer import make_reviewer

AGENT_FACTORIES = {
    "researcher": make_researcher,
    "writer": make_writer,
    "reviewer": make_reviewer,
}