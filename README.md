# multiagent-scaffold 使用手册

> 一套**配置驱动(config-driven)的多 agent 系统**:三个 agent 像流水线一样接力,
> researcher 先从你的本地知识库检索(RAG),writer 写文章,reviewer 审稿;
> 审不过就打回 writer 重写,直到通过或撞到次数上限。
> **谁先跑、谁连谁、循环怎么转,全写在 `config.yaml` 里,不写死在代码里。**

---

## 目录

1. [30 秒看懂整体](#1-30-秒看懂整体)
2. [核心概念:State 是一块"共享白板"](#2-核心概念state-是一块共享白板)
3. [每个文件干什么(文件地图)](#3-每个文件干什么文件地图)
4. [跑一次 `main.py` 到底发生了什么](#4-跑一次-mainpy-到底发生了什么)
5. ["配置驱动"是什么意思:config → 图 的翻译表](#5-配置驱动是什么意思config--图-的翻译表)
6. [How-To · 常见修改任务](#6-how-to-常见修改任务)
   - [A. 换某个 agent 用的模型](#a-换某个-agent-用的模型)
   - [B. 改 / 替换 / 删除 / 新增循环](#b-改--替换--删除--新增循环)
   - [C. 给 agent 加新能力(工具 / skill)](#c-给-agent-加新能力工具--skill)
   - [D. 加一个全新的 agent](#d-加一个全新的-agent)
   - [E. 换 / 加知识库内容](#e-换--加知识库内容)
   - [F. 调检索参数(top_k / chunk)](#f-调检索参数top_k--chunk)
7. [Windows / Ollama 速查 & 常见报错](#7-windows--ollama-速查--常见报错)
8. [词汇表](#8-词汇表)

---

## 1. 30 秒看懂整体

这个项目就是一条**自动写稿流水线**,三个工人(agent)依次干活:

| Agent | 它干的事 | 用到的能力 |
|---|---|---|
| **researcher** | 拿你的主题去**知识库里检索**相关资料,整理成要点 | RAG 检索(retriever 这个"工具") |
| **writer** | 把 researcher 的要点写成一篇文章;被打回时**根据审稿意见重写** | 纯 LLM |
| **reviewer** | 给文章打分,输出"通过 / 打回"(pass / revise)+ 修改建议 | 纯 LLM |

reviewer 后面有个**裁判(router)**:如果判 revise 且还没用完重写预算 → 退回 writer 重写;否则 → 结束。这就是"循环"。

```
config.yaml  ──(graph.py 读取并翻译)──►  一张可运行的图 app
                                              │
   main.py 种入初始 State {topic, ...} ───────┘  开始跑
                                              ▼
   START
     │
     ▼
   researcher ──写 research──► writer ──写 draft──► reviewer
   (查知识库 RAG)              (写/改文章)          (判 pass/revise)
        ▲                        ▲                     │
        │ retriever(工具/skill)  │                     │ 写 verdict / review / revision_count
        │                        │                     ▼
   Chroma 向量库            └─── "revise" 打回 ───  review_router (routing.py)
   (来自 knowledge/)                               "没过 且 没超预算?"
                                                    │                 │
                                                "revise"           "pass"
                                                回 writer 重写       去 END 结束
```

**记住这一句话**:`config.yaml` 是控制台,`graph.py` 是组装器,三个 agent 是工人,它们之间靠一块叫 **State 的共享白板**传递数据。

---

## 2. 核心概念:State 是一块"共享白板"

这是理解一切的钥匙。**agent 之间不直接互相调用**。它们都对着同一块白板(`State`)读和写:

- 每个 agent 是一个函数,输入是**当前整块 State**,输出是**它要更新的几个字段**(一个小字典)。
- LangGraph 会把这个小字典**合并**进白板。下一个 agent 再读这块更新后的白板。

举例:`researcher` 返回 `{"research": "..."}`,白板上 `research` 字段就被填上;接着 `writer` 读白板上的 `research` 来写稿。

> ⚠️ **正因为这样,字段名极其重要。** researcher 写 `research`、writer 读 `research`,两边名字一致才接得上;**只要有一个名字拼错,链子就会"静默断裂"——不报错,但后面读到空**。我们这一路调试时反复强调这点,原因就在这里。

**白板上有哪些字段、谁写谁读**(定义在 `state.py`):

| 字段 | 谁写 | 谁读 | 含义 |
|---|---|---|---|
| `topic` | 你(`main.py` 初始化) | researcher | 要研究/写作的主题 |
| `research` | researcher | writer | 检索+整理后的资料要点 |
| `draft` | writer | reviewer | 写出来的文章 |
| `review` | reviewer | writer(重写时) | reviewer 的修改建议 |
| `verdict` | reviewer | **router** | `"pass"` 或 `"revise"` |
| `revision_count` | reviewer | **router** | reviewer 累计判了几次 revise |
| `max_revisions` | 你(`main.py` 从 config 种入) | **router** | 重写次数预算(防死循环) |

`state.py` 长这样(`total=False` 表示这些字段都不强制一开始就有,谁用到谁填):

```python
from typing import TypedDict

class State(TypedDict, total=False):
    topic: str
    research: str
    draft: str
    review: str
    verdict: str          # "pass" / "revise"
    revision_count: int   # reviewer 已累计判 revise 的次数
    max_revisions: int    # 预算(由 main 从 config 读入种进来)
```

---

## 3. 每个文件干什么(文件地图)

```
multiagent-scaffold/
├── config.yaml          ← 【控制台】改行为基本只动这里
├── graph.py             ← 【组装器】把 config 翻译成可运行的图(很少需要改)
├── registry.py          ← 【通讯录】agent 名字 → 工厂函数
├── routing.py           ← 【裁判】循环的判断逻辑(router 函数)
├── state.py             ← 【白板的字段表】定义 State 有哪些字段
├── main.py              ← 【入口】种入初始 State、跑图、打印结果
├── llm_factory.py       ← 据 config 造出对应的 ChatOllama 模型
│
├── agents/              ← 【工人们】每个 agent 一个文件
│   ├── researcher.py
│   ├── writer.py
│   └── reviewer.py
│
├── embeddings.py        ← embedding 入口(nomic-embed-text);灌库&检索共用
├── vectorstore.py       ← 打开/创建 Chroma 向量库(collection: knowledge_base)
├── ingest.py            ← 把 knowledge/ 的文档切块、向量化、灌进库(改了知识就重跑)
├── tools/
│   └── retriever.py     ← 【researcher 的"工具/skill"】输入问题→返回资料文本
│
├── knowledge/           ← 你的知识来源文档(.md / .txt)
└── chroma_db/           ← ingest 生成的向量库(别手动改,已 .gitignore)
```

逐个说明它们的"职责":

| 文件 | 职责(一句话) | 你什么时候会动它 |
|---|---|---|
| **config.yaml** | 控制台:定义入口、每个 agent 用什么模型、边怎么连、循环、预算 | **换模型、改循环、加 agent 时——大部分修改都在这** |
| **graph.py** | 组装器:读 config → `StateGraph(State)` → 加节点/边 → `compile()`,产出可运行的 `app` | 很少;只有要支持**新的配置语法**时才动 |
| **registry.py** | 通讯录:把 config 里的 agent 名字(字符串)对应到真正的工厂函数 | **加新 agent 时**(注册它) |
| **routing.py** | 裁判:`review_router(state)` 看白板决定下一步去哪;`ROUTERS` 把名字映射到函数 | **改循环停止逻辑时** |
| **state.py** | 白板字段表 | **新增需要传递的字段时** |
| **agents/\*.py** | 工人:每个是 `make_xxx(llm, ...)` 工厂,返回一个 `node(state)->小字典` 的函数 | **改某个 agent 的行为/prompt/加工具时** |
| **llm_factory.py** | 据 agent 的配置造出 `ChatOllama`(内含 `base_url` 设置) | 几乎不动 |
| **embeddings.py** | 统一的 embedding 入口 | 换 embedding 模型时(换了要重灌库!) |
| **vectorstore.py** | Chroma 向量库的统一入口 | 改库名/存储路径时 |
| **ingest.py** | 灌库脚本 | **每次改了 knowledge/ 内容后跑一次** |
| **tools/retriever.py** | researcher 的检索工具 | 改检索格式时 |
| **main.py** | 入口:种 State、跑、打印 | 改主题、改打印方式时 |

**"工厂函数(factory)"是什么?** 每个 agent 文件里都有个 `make_xxx(llm)`。它不是 agent 本身,而是"**用某个模型造出一个 agent**"的生产线。为什么要这层?因为这样**模型可以从外面(config)注入**——同一个 reviewer,你想用 4b 还是 27b,在 config 里换一下,`graph.py` 就用对应模型去 `make_reviewer(llm)`。这正是"配置驱动"能成立的关键。

```python
# agents/writer.py 的结构(典型工厂)
def make_writer(llm):                # ← 工厂:吃一个模型
    def writer(state):               # ← 真正的 agent 节点:吃白板,吐更新
        research = state.get("research", "")
        feedback = state.get("review", "")   # 重写时才有
        ...
        resp = llm.invoke(prompt)
        return {"draft": resp.content}        # ← 只更新 draft 这一格
    return writer                    # ← 把造好的 agent 交回去
```

---

## 4. 跑一次 `main.py` 到底发生了什么

按顺序拆解 `python main.py`:

1. **`build_graph()`**(在 `graph.py`):读 `config.yaml` → 创建 `StateGraph(State)` → 按 config 加节点、加普通边、加条件边 → `compile(checkpointer=MemorySaver())`。**到此引擎就绪**,得到一个能跑的 `app`。
2. **`main.py` 种入初始白板**:`init = {"topic": ..., "revision_count": 0, "max_revisions": <从 config.settings 读>}`。
3. **`app.stream(init, config=...)` 开跑**,数据在白板上一站站流:
   - `START → researcher`:检索知识库,写入 `research`。
   - `researcher → writer`:读 `research`,写入 `draft`。
   - `writer → reviewer`:读 `draft`,写入 `verdict` / `review` / `revision_count`。
   - `reviewer →(review_router 判断)`:
     - 判 `revise` 且 `revision_count <= max_revisions` → **回到 writer**(带着 `review` 重写)。
     - 否则(判 pass / 超预算)→ **END**。
4. **打印最终白板**:`research` / `draft` / `review` / `verdict` / 重写次数。

`thread_id`(`config={"configurable": {"thread_id": "demo-1"}}`)的作用:配合 `MemorySaver`,让这一次运行的白板被记住,所以跑完能用 `app.get_state(config).values` 把最终全量状态取出来。

`recursion_limit`(默认 25,我们设了 50):循环会反复跑节点,这是 LangGraph 的"最多走多少步"安全阀,防止真死循环时把程序卡死。

---

## 5. "配置驱动"是什么意思:config → 图 的翻译表

`graph.py` 的本质就是一台翻译机:把 `config.yaml` 里的每一块,翻译成一句建图的代码。看懂这张表,你就知道**改 config 的哪一块 = 改图的什么**:

| config.yaml 里的块 | graph.py 翻译成 | 效果 |
|---|---|---|
| `entry: researcher` | `g.add_edge(START, "researcher")` | 从哪个 agent 开始 |
| `agents.<名>.model: gemma3:4b` | `make_llm(配置)` 选这个模型 | 这个 agent 用哪个模型 |
| `agents.<名>.<其它字段>`(如 `top_k`) | 作为 **kwargs 传给工厂 `make_<名>(llm, top_k=...)` | 给 agent / 它的工具传参数 |
| `edges: - [a, b]` | `g.add_edge("a", "b")`(**固定**边) | a 跑完永远走 b |
| `conditional_edges` | `g.add_conditional_edges(source, ROUTERS[router], paths)` | **按情况分流 / 循环** |
| `settings.max_revisions` | `main.py` 读出来种进 State | 循环预算 |

你现在的 `config.yaml` 大致是:

```yaml
entry: researcher

agents:
  researcher:
    model: gemma3:4b
    top_k: 4              # 非 model 字段 → 作为 kwarg 传给 make_researcher
  writer:
    model: gemma3:27b
  reviewer:
    model: gemma3:4b

edges:                    # 固定边
  - [researcher, writer]
  - [writer, reviewer]

conditional_edges:        # 条件边(循环就在这)
  - source: reviewer       # 从 reviewer 出发判断
    router: review_router  # 用哪个 router(名字 → routing.py 的 ROUTERS 里找)
    paths:                 # router 返回的标签 → 去哪
      revise: writer       # 返回 "revise" → 回 writer 重写
      pass: END            # 返回 "pass"  → 结束

settings:
  max_revisions: 2
```

`graph.py` 里负责翻译的关键片段(理解即可,一般不用改):

```python
# 1) 加节点:model 以外的字段(如 top_k)透传给工厂当 kwargs
for name, acfg in cfg["agents"].items():
    llm = make_llm(acfg)
    factory = AGENT_FACTORIES[name]
    kwargs = {k: v for k, v in acfg.items() if k != "model"}
    g.add_node(name, factory(llm, **kwargs))

# 2) 普通边
for src, dst in cfg.get("edges", []):
    g.add_edge(src, dst)

# 3) 条件边:按名字取 router,把字符串 "END" 换成真的 END 常量
for ce in cfg.get("conditional_edges", []):
    router = ROUTERS[ce["router"]]
    path_map = {label: (END if target == "END" else target)
                for label, target in ce["paths"].items()}
    g.add_conditional_edges(ce["source"], router, path_map)
```

---

## 6. How-To · 常见修改任务

### A. 换某个 agent 用的模型

**在哪改:** `config.yaml` 的 `agents.<名>.model`。**不用动任何代码。**

例:想让审稿更严谨,把 reviewer 换成更强的 27b:

```yaml
agents:
  reviewer:
    model: gemma3:27b      # 原来是 gemma3:4b
```

**为什么不用改代码:** `graph.py` 会把这个 agent 的配置交给 `make_llm`,`make_llm` 据 `model` 字段造出对应的 `ChatOllama`,再交给 `make_reviewer(llm)`。模型从外面注入,agent 代码完全不知道也不关心用的是哪个模型。

**注意事项:**
- 模型必须先在 Ollama 里有:`ollama list` 看一眼,没有就 `ollama pull gemma3:27b`。
- **显存(VRAM):** 循环里 writer 会被反复调用,如果每个 agent 都用大模型,显存吃紧。常见做法是**混搭**——便宜的活(researcher 整理、reviewer 判定)用 4b,最关键的活(writer 产出正文)用 27b。你现在就是这么配的。
- 改完直接重跑 `python main.py` 即可。

> 想换成别的模型家族(比如 `qwen3`)也一样,只要 Ollama 里 `pull` 过、`ollama list` 里有,把 `model:` 写成那个名字就行。

---

### B. 改 / 替换 / 删除 / 新增循环

**先理解:一个循环由 4 个零件配合而成。** 改循环 = 改其中某个零件。

| 零件 | 在哪 | 作用 |
|---|---|---|
| ① 信号产生者 | `agents/reviewer.py` | reviewer 往白板写 `verdict`(pass/revise) |
| ② 裁判读的字段 | `state.py` | `verdict` / `revision_count` / `max_revisions` |
| ③ 判断逻辑 | `routing.py` 的 `review_router` | 看白板,返回一个标签(`"revise"`/`"pass"`) |
| ④ 接线 | `config.yaml` 的 `conditional_edges` | 把 `source → router → {标签: 去向}` 连起来 |

你现在的裁判逻辑(`routing.py`):

```python
def review_router(state):
    verdict = state.get("verdict", "pass")
    count   = state.get("revision_count", 0)
    budget  = state.get("max_revisions", 2)
    if verdict == "revise" and count <= budget:   # 没过 且 没超预算 → 重写
        return "revise"
    return "pass"                                  # 否则 → 结束
```

#### B-1. 只想改"最多重写几次"(最常见)
**在哪改:** `config.yaml` 的 `settings.max_revisions`。改个数就行。

#### B-2. 想改"少绕一轮"(精确控制轮数)
**在哪改:** `routing.py` 里 `count <= budget` ↔ `count < budget`。
`<=` 时 `max_revisions=2` 实际允许**重写 2 次**;改成 `<` 就是 1 次。(还记得吗——`revision_count` 数的是"reviewer 判了几次 revise",撞预算结束时它会比"真实重写次数"多 1,因为最后那次 revise 被记数但没被执行。)

#### B-3. 想改"被打回后去哪"(而不是回 writer)
**在哪改:** `config.yaml` 的 `conditional_edges.paths`。
例:被打回时先送到一个新的 `editor`(润色)agent,而不是直接回 writer:

```yaml
conditional_edges:
  - source: reviewer
    router: review_router
    paths:
      revise: editor      # ← 改这里(前提:你已经加了 editor 这个 agent,见 D 节)
      pass: END
```

#### B-4. 想换一套**完全不同的判断逻辑**
**在哪改:** `routing.py` 的 `review_router` 函数体。它就是普通 Python,返回一个字符串标签即可。
例:除了 reviewer 说要改,还要求"草稿太短也强制重写":

```python
def review_router(state):
    verdict = state.get("verdict", "pass")
    count   = state.get("revision_count", 0)
    budget  = state.get("max_revisions", 2)
    too_short = len(state.get("draft", "")) < 300   # 新增:太短也算不合格

    if (verdict == "revise" or too_short) and count <= budget:
        return "revise"
    return "pass"
```

#### B-5. 想**彻底关掉循环**(变回线性流水线)
- **最省事(零代码):** `config.yaml` 把 `settings.max_revisions: 0`。这样 reviewer 第一次判 revise → `count` 变 1 → `1 <= 0` 为假 → 直接 `pass` 结束,永远不会重写。reviewer 仍会跑一次给你打个分。
- **结构上移除:** 删掉整个 `conditional_edges` 块。**注意**:这样 reviewer 就没有出边了,流程会在 reviewer 之后自然结束(它成了终点)。如果你想用普通 `edges` 显式写 `reviewer → END`,需要先让 `graph.py` 的普通边也支持把字符串 `"END"` 换成 `END` 常量(它目前只在条件边里做了这个转换)。所以**关循环优先用 `max_revisions: 0` 这条**,最稳。

#### B-6. 想**新增一个完全不同的循环 / 分叉**(进阶)
配方:写一个新 router 函数 → 注册进 `ROUTERS` → 在 `config.yaml` 加一条 `conditional_edges`。
例:让 researcher 之后判断"资料够不够",不够就……(伪示意)

```python
# routing.py
def research_router(state):
    if len(state.get("research", "")) < 100:
        return "retry"      # 资料太少
    return "ok"

ROUTERS = {
    "review_router": review_router,
    "research_router": research_router,   # ← 注册新的
}
```
```yaml
# config.yaml 再加一条
conditional_edges:
  - source: researcher
    router: research_router
    paths:
      retry: researcher     # 资料不够 → 再查一次(自己回到自己)
      ok: writer
  - source: reviewer        # 原来那条保留
    router: review_router
    paths:
      revise: writer
      pass: END
```

> **一句话记忆:循环/分叉的"该不该跳、跳去哪"的逻辑在 `routing.py`,而"哪个节点接哪个 router、标签对应哪个去向"的接线在 `config.yaml`。**

---

### C. 给 agent 加新能力(工具 / skill)

这里的"skill"指**一个 agent 能调用的工具**——比如 researcher 用的 `retriever` 就是它的 skill(给它一句话,它返回一段资料)。**任何 Python 能做的事都能做成工具**:真·联网搜索、计算器、查数据库、查另一个向量库……

**套路永远是三步**(完全照着 `tools/retriever.py` 的模式):

#### 第 1 步:把工具写成 `tools/` 里的一个工厂
工具 = 一个工厂函数,返回一个"输入 → 输出文本"的小函数。
例:做一个"术语表查询"工具,让 agent 能展开缩写:

```python
# tools/glossary.py
def make_glossary():
    table = {
        "RAG": "Retrieval-Augmented Generation,检索增强生成",
        "MoE": "Mixture of Experts,混合专家",
        "VRAM": "显存",
    }
    def lookup(term: str) -> str:
        return table.get(term.strip().upper(), f"(术语表里没有「{term}」)")
    return lookup
```

#### 第 2 步:在某个 agent 的工厂里建好工具,在节点里调用它
把工具的输出**喂进 prompt**(和 researcher 把检索结果喂进 prompt 一模一样):

```python
# agents/writer.py —— 给 writer 加上术语表能力
from langchain_core.messages import SystemMessage, HumanMessage
from tools.glossary import make_glossary          # ← 引入工具

def make_writer(llm):
    glossary = make_glossary()                     # ← 工厂里建一次

    def writer(state):
        research = state.get("research", "")
        feedback = state.get("review", "")
        # 用工具:把出现的缩写解释附在资料后面
        hint = "术语提示:" + glossary("MoE")        # ← 调用工具
        extra = f"\n\n审稿意见(请据此修改):\n{feedback}" if feedback else ""
        prompt = [
            SystemMessage(content="你是写作者,根据资料写一篇结构清晰的短文。"),
            HumanMessage(content=f"资料:\n{research}\n{hint}{extra}\n\n请输出正文。"),
        ]
        resp = llm.invoke(prompt)
        return {"draft": resp.content}
    return writer
```

#### 第 3 步(可选):如果工具需要参数,从 config 传进来
还记得 researcher 的 `top_k` 吗?那就是"从 config 给工具传参"的范例。机制是:`config.yaml` 里 agent 名下的**非 `model` 字段会作为 kwargs 传给工厂**。

```yaml
agents:
  researcher:
    model: gemma3:4b
    top_k: 4          # → make_researcher(llm, top_k=4)
```
```python
def make_researcher(llm, top_k: int = 4):   # ← 工厂接住这个 kwarg
    search = make_retriever(k=top_k)
    ...
```

> ⚠️ **关键坑:** 如果你在 config.yaml 里给某个 agent 加了一个非 model 字段(比如给 writer 加 `style: formal`),那么这个 agent 的工厂**必须能接住这个关键字参数**,否则 `graph.py` 调 `make_writer(llm, style="formal")` 会报 `TypeError: unexpected keyword argument 'style'`。两种解法:① 在工厂签名里加 `style="..."`;② 或给工厂统一加 `**kwargs` 来兜底未用到的参数。

**几个真实可做的工具点子:**
- 真·联网搜索:`tools/web_search.py` 里用 `requests` 调一个搜索 API,返回摘要文本(替换/补充那个早期的假 web_search)。
- 第二个知识库:再建一个 `get_vectorstore()` 指向不同 collection,做成第二个 retriever 给另一个 agent 用。
- 计算/校验:让 reviewer 调一个"字数统计/敏感词检查"工具,把结果纳入判定。

---

### D. 加一个全新的 agent

配方四步。以"在 writer 和 reviewer 之间加一个 `editor`(润色)agent"为例:

**第 1 步:写 `agents/editor.py`**(决定它读白板哪格、写哪格)

```python
# agents/editor.py
from langchain_core.messages import SystemMessage, HumanMessage

def make_editor(llm):
    def editor(state):
        draft = state.get("draft", "")
        prompt = [
            SystemMessage(content="你是文字编辑,只做润色:改通顺、去冗余,不改变事实和结构。"),
            HumanMessage(content=f"请润色下面的文章:\n{draft}"),
        ]
        resp = llm.invoke(prompt)
        return {"draft": resp.content}      # ← 仍写回 draft(覆盖)
    return editor
```

**第 2 步:在 `registry.py` 注册**(让 config 能用名字找到它)

```python
from agents.editor import make_editor
AGENT_FACTORIES = {
    "researcher": make_researcher,
    "writer": make_writer,
    "editor": make_editor,          # ← 新增
    "reviewer": make_reviewer,
}
```

**第 3 步:在 `config.yaml` 里给它配模型 + 接进流程**

```yaml
agents:
  ...
  editor:
    model: gemma3:4b      # ← 新增
  ...

edges:
  - [researcher, writer]
  - [writer, editor]      # ← 改:writer 先到 editor
  - [editor, reviewer]    # ← 改:editor 再到 reviewer
```

**第 4 步(按需):如果新 agent 要写一个新字段,去 `state.py` 加上。**
(本例 editor 只覆盖 `draft`,不用加新字段。)

> 加完重跑 `main.py`,你会在节点轨迹里看到 `editor` 出现在 `writer` 和 `reviewer` 之间。

---

### E. 换 / 加知识库内容

researcher 检索的就是 `knowledge/` 里、经 `ingest.py` 灌进 Chroma 的内容。

1. 把新的 `.md` / `.txt` 丢进 `knowledge/`(或删掉不想要的)。
2. 重新灌库:
   ```
   python ingest.py
   ```
3. **注意 `ingest.py` 是追加(append),不去重。** 想干净重建,先删库再灌:
   ```
   if (Test-Path chroma_db) { Remove-Item -Recurse -Force chroma_db }
   python ingest.py
   ```
4. **同一个 embedding 模型铁律:** 如果你改了 `embeddings.py` 里的 embedding 模型,**必须**删掉 `chroma_db/` 重灌——旧向量是用旧模型算的,和新模型的向量空间对不上,检索会失效。

> 顺手提示:你库里有些从网页复制来的噪声行(比如 `Press enter or click to view image...`)。清掉它们能让检索质量更高——编辑 `knowledge/` 里的文档删掉这类行,再 `ingest.py` 重灌即可。

---

### F. 调检索参数(top_k / chunk)

| 想调什么 | 在哪 | 说明 |
|---|---|---|
| **检索回几块**(top_k) | `config.yaml` → `agents.researcher.top_k` | 大 = 资料更多但更杂、更费 token;小 = 更聚焦。常用 3–5。改完直接重跑,**不用重灌库**。 |
| **每块多大 / 重叠多少**(chunk) | `ingest.py` → `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)` | 影响切分粒度。**改了必须删 `chroma_db/` 重灌**(因为入库时就按这个切的)。 |

---

## 7. Windows / Ollama 速查 & 常见报错

**速查:**
- 激活虚拟环境:`.venv\Scripts\activate`
- 装包:`python -m pip install <包名>`
- 创建任何 `ChatOllama` / `OllamaEmbeddings` **都必须带** `base_url="http://127.0.0.1:11434"`(否则 localhost 走 IPv6 报 `WinError 10049`)。
- 控制台中文乱码:本会话先跑一次 `chcp 65001`。
- 看有哪些模型:`ollama list`;拉模型:`ollama pull <模型名>`。
- PowerShell 里丢弃报错用 `2>$null`(**不是** cmd 的 `2>nul`)。

**常见报错对照:**

| 报错 | 多半的原因 | 怎么修 |
|---|---|---|
| `KeyError: 'xxx'` | 白板字段名拼错 / 两端不一致 | 对齐 `state.py` 与各 agent 读写的字段名 |
| `chromadb ... InvalidArgumentError: name ... Got: kb` | collection 名 < 3 个字符 | 用 ≥3 字符的名字(我们用 `knowledge_base`) |
| `WinError 10049` | `ChatOllama`/`OllamaEmbeddings` 没写 `base_url` | 补上 `base_url="http://127.0.0.1:11434"` |
| `TypeError: ... unexpected keyword argument` | config 里给 agent 加了字段,但工厂没接住 | 工厂签名加该参数,或加 `**kwargs` |
| `Recursion limit ... reached` | 循环停不下来 | 检查 router 逻辑 / `max_revisions`;`main.py` 里调大 `recursion_limit` |
| `ModuleNotFoundError` | 没装包 / `tools/` 缺 `__init__.py` | `pip install ...`;给 `tools/` 建空的 `__init__.py` |
| 检索结果全是噪声 / 不相关 | ingest 和检索用了不同 embedding 模型 | 统一模型,删 `chroma_db/` 重灌 |

---

## 8. 词汇表

- **agent**:流水线上的一个工人。本项目里是一个 `node(state)->{更新}` 的函数。
- **工厂 / factory**:`make_xxx(llm)`,用注入的模型"生产"出一个 agent。让模型可从 config 注入。
- **State / 白板**:在 agent 之间传递的共享字典。每个 agent 读它、返回要更新的几格。
- **node / 节点**:图里的一个执行步骤(通常就是一个 agent)。
- **edge / 边**:节点之间的连线。**普通边**(固定走向)vs **条件边**(按 state 分流)。
- **conditional edge / 条件边**:跑完某节点后,看 state 动态决定下一步去哪——循环就靠它。
- **router / 路由函数**:条件边的判断函数,输入 state、返回一个字符串标签;标签再映射到去向。
- **LLM**:大语言模型(这里是本地 Ollama 上的 `gemma3` 等)。
- **RAG(Retrieval-Augmented Generation)**:回答前先去知识库"查资料",再带着资料让模型作答。
- **embedding / 向量**:把一段文字变成一串数字(本项目 768 维),意思相近的文字向量也相近。
- **vector store / 向量库**:存这些向量、支持"找最相近的几条"的数据库(本项目用 Chroma)。
- **chunk / 块**:长文档被切成的小段,以块为单位入库和检索。
- **top_k**:每次检索捞回最相近的 k 块。
- **checkpointer / MemorySaver**:记住每次运行白板状态的组件;配合 `thread_id` 使用。
- **thread_id**:一次运行(会话)的标识,让状态能被存取。

---

*改任何东西的总原则:先想清楚要动的是"行为(config.yaml)"、"工人(agents/)"、"判断(routing.py)"还是"白板(state.py)";大多数改动只动 config.yaml。改完小步跑一次验证,坏了 `git checkout` 即可还原。*