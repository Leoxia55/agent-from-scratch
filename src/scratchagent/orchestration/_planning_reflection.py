"""智能体的规划与反思工具"""

from typing import Literal

from pydantic import BaseModel

from ..tools import tool


class Task(BaseModel):
    content: str
    status: Literal["pending", "in_progress", "completed"]

    def __str__(self):
        if self.status == "pending":
            return f"[ ] {self.content}"
        elif self.status == "in_progress":
            return f"[>] **{self.content}**"
        elif self.status == "completed":
            return f"[X] ~~{self.content}~~"
        return self.content


@tool
def create_tasks(tasks: list[Task]) -> str:
    """Create or update a task plan.

    WHEN TO USE:
    - Complex queries requiring multiple steps of research
    - Questions that need to combine information from different sources

    WHEN NOT TO USE:
    - Simple questions answerable with a single search
    - Tasks with obvious, straightforward procedures

    HOW TO USE:
    - Regenerate the entire task list with updated statuses
    - Mark completed tasks as 'completed'
    - Mark the next task to work on as 'in_progress'
    - Keep future tasks as 'pending'
    """
    normalized_tasks = [
        task if isinstance(task, Task) else Task.model_validate(task) for task in tasks
    ]
    plan = "\n".join(str(task) for task in normalized_tasks)
    print(f"\n[Planning] Task list:\n{plan}\n", flush=True)
    return plan


@tool
def reflection(analysis: str, need_replan: bool = False) -> str:
    """Pause and analyze progress before continuing.

    WHEN TO USE:
    1. PROGRESS REVIEW - After completing a meaningful step
       "Kipchoge's record found: 2:01:09. Moving to moon distance research."

    2. ERROR ANALYSIS - When a tool fails or returns unexpected results
       "Wikipedia tool failed. Cause: service unavailable. Alternative: use web search."

    3. RESULT SYNTHESIS - When combining information from multiple sources
       "Two different moon distances found. Problem asks for closest approach, so using perigee: 356,500km."

    4. SELF CHECK - Before providing final answer
       "Have all required data: marathon pace 20.81km/h, moon distance 356,500km. Ready to calculate."

    WHEN NOT TO USE:
    - After every single tool call (excessive overhead)
    - During simple, straightforward operations
    - When everything is proceeding as expected

    Args:
        analysis: Your assessment of current situation and next direction
        need_replan: Set True if the current plan needs modification
    """
    if need_replan:
        return f"Reflection recorded (REPLAN NEEDED): {analysis}"
    return f"Reflection recorded: {analysis}"
