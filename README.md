## 如何新增一个 agent
1. 在 agents/ 写一个 agent 函数(或工厂)
2. 在 registry.py 登记:名字 → 函数
3. 在 config.yaml 把它接进 edges / agents
   —— 全程不用动 graph.py