# 04. E2B 与 Skills

E2B 为 Agent 提供隔离的 Python 运行环境；Skills 用目录中的 `SKILL.md` 描述可复用的工作方法，并在需要时上传到沙箱。

## 1. 使用 E2B

```python
import asyncio

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config


async def main() -> None:
    config = resolve_model_config(Provider.OPENAI_COMPAT, "gpt-4o-mini")
    client = LlmClient(default_config=config)
    agent = Agent(
        model=client,
        instruction="需要运行 Python 时使用 E2B 工具。",
        code_execution="e2b",
    )
    result = await agent.run("用 Python 计算前 20 个斐波那契数。")
    print(result.output)


if __name__ == "__main__":
    asyncio.run(main())
```

配置 `E2B_API_KEY`，可选 `E2B_TEMPLATE_ID`/`E2B_TEMPLATE`。Agent 会自动注册 `execute_python_in_e2b`、`base_e2b_tool` 和 `upload_file_to_e2b`，并在自己创建的环境上结束时调用 `kill()`。

## 2. 把 Skills 放进沙箱

目录示例：

```text
skills/
  data-cleaning/
    SKILL.md
```

`SKILL.md` 必须包含简单 frontmatter：

```markdown
---
name: data-cleaning
description: 清洗 CSV 并检查缺失值
---

先读取列名，再输出缺失值统计。
```

```python
from scratchagent import discover_skills, generate_skills_prompt

skills = discover_skills("skills")
print(generate_skills_prompt(skills))
agent = Agent(model=client, code_execution="e2b", skills_path="skills")
```

Skills 只会扫描 `skills/` 的直接子目录和其中的 `SKILL.md`；隐藏目录会被忽略。内容最终作为说明注入 prompt，并上传到 `/home/user/skills`。

下一步：[多智能体](05-multi-agent.md)。

