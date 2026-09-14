"""skill-agent 示例：演示技能发现与注入

原理
----
框架支持将「技能」以目录形式组织（每个子目录含一个 SKILL.md，其 YAML
frontmatter 需包含 name 与 description）。通过 skills_path 指定技能根目录后：
  - discover_skills 扫描目录，解析每个 SKILL.md 的 frontmatter；
  - generate_skills_prompt 生成技能说明，自动注入到 Agent 的指令中；
  - 若启用 E2B，技能文件会被上传到沙箱供代码直接 import 使用。

本示例演示纯「发现 + 注入」路径（不依赖沙箱），Agent 会被告知可用技能。

关键 API
--------
  discover_skills(skills_path)
  generate_skills_prompt(skills)
  Agent(skills_path=...)

运行方式
--------
  cd D:/00_persist/agent-from-scratch
  .venv/Scripts/python.exe examples/skill_agent.py
"""

import asyncio
from pathlib import Path

from scratchagent import Agent
from scratchagent.llm import LlmClient, Provider, resolve_model_config
from scratchagent.skills import discover_skills, generate_skills_prompt


async def discover_skills_agent() -> None:
    openai_client = LlmClient(
        default_config=resolve_model_config(
            provider=Provider.OPENAI_COMPAT, model="gpt-5.5"
        )
    )

    # 示范技能目录（相对本文件定位）
    skills_path = Path(__file__).parent / "skills"

    # 手动演示发现与 prompt 生成
    skills = discover_skills(skills_path)
    print(f"[Skill] 发现 {len(skills)} 个技能：")
    for s in skills:
        print(f"   - {s.name}: {s.description}")
    print("\n[Skill] 生成的提示词片段：")
    print(generate_skills_prompt(skills))

    agent = Agent(
        model=openai_client,
        instruction="You are a helpful assistant.",
        skills_path=str(skills_path),
    )

    user_input = "你能使用哪些技能？请介绍一下。"
    result = await agent.run(user_input)
    print(f"\n最终结果是：{result.output}")


if __name__ == "__main__":
    asyncio.run(discover_skills_agent())
