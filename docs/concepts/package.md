# 类型注解规范（Package & Annotation Conventions）

> 本文档描述 `scratchagent` 项目采用的**类型注解规范**与**模块/包命名约定**，是教学示范项目「统一规范」的一部分。
> 适用版本：Python 3.13（`requires-python = ">=3.13.0, <3.14"`）。

---

## 1. 类型注解总则

项目统一采用**现代类型注解语法**，遵循以下 PEP 标准：

| PEP | 内容 | 项目约定 |
|-----|------|---------|
| **PEP 484** | 类型注解基础（`->`、`: type`） | ✅ 全面使用 |
| **PEP 585** | 内置泛型（`list[str]`、`dict[str, int]`） | ✅ 全面使用，**禁用**旧式 `typing.List/Dict` |
| **PEP 604** | 联合类型（`str \| None`） | ✅ 全面使用，**禁用**旧式 `typing.Optional/Union` |
| **PEP 695** | `type` 类型别名语句 | ✅ 仅 `types.py:49` 一处，作为教学示范 |

### 1.1 核心原则

> **类型信息写进「签名」，不写进「docstring」。**

docstring 只描述**语义**（这个参数是什么、为什么），类型由签名里的注解承担。这是 PEP 484 的明确要求，也让 mypy、IDE 能直接读取类型做静态检查。

### 1.2 反例与正例

```python
# ❌ 旧式：类型写在 docstring 里，机器读不到
def get_embeddings(texts, model="..."):
    """...
    Args:
        texts (list of str): 待嵌入的文本列表.   # ← "list of str" 是自然语言，非类型语法
    """
    ...

# ✅ 规范：类型写进签名，docstring 只讲语义
def get_embeddings(texts: str | list[str], model: str = "...") -> np.ndarray:
    """...
    Args:
        texts: 待嵌入的文本列表.
    """
    ...
```

---

## 2. 具体语法约定

### 2.1 内置泛型（PEP 585）

使用 `list[str]`、`dict[str, int]`、`tuple[int, str]`、`set[str]` 等**小写内置泛型**，**不再**从 `typing` 导入 `List`/`Dict`/`Tuple`/`Set`/`Optional`/`Union`。

```python
def fixed_length_chunking(text: str, chunk_size: int = 200, overlap: int = 50) -> list[str]:
    ...
```

### 2.2 联合类型（PEP 604）

使用 `|` 连接联合类型，**不再**写 `Union[...]` 或 `Optional[...]`。

```python
def get_embeddings(texts: str | list[str], ...) -> np.ndarray:
    ...

def load_skill(skill_dir: Path) -> SkillInfo | None:   # 而非 Optional[SkillInfo]
    ...
```

### 2.3 类型别名（PEP 695）

Python 3.12+ 的 `type` 语句可用于定义类型别名。项目中唯一的一处在 `types.py`：

```python
# PEP-695 类型别名 + PEP-604 联合类型
type ContentItem = Message | ToolCall | ToolResult | SummaryMessage
```

> 教学提示：`type X = ...` 是 PEP 695（3.12）的新语法，等价于旧式的
> `ContentItem = TypeAlias`（PEP 613）或 `from typing import TypeAlias` 的用法，
> 但更简洁。项目以此作为「新旧语法演进」的教学锚点。

### 2.4 `TypedDict`（异构字典）

当函数返回的字典**每个键有固定类型**时，用 `TypedDict` 精确描述结构，而不是笼统的 `dict[str, Any]`：

```python
from typing import TypedDict

class SearchResult(TypedDict):
    """向量搜索结果：一个文本块及其与查询的相似度."""
    chunk: str
    similarity: float

def vector_search(...) -> list[SearchResult]:
    ...
```

> 教学提示：`TypedDict` 在运行时就是普通 `dict`，只为 mypy 提供精确结构。
> 它能避免 `dict[str, str | float]` 这种「无法区分哪个键是 str、哪个是 float」的笼统标注。

### 2.5 协变容器：`Sequence` vs `list`

**可变容器（`list`）在类型上是「不变（invariant）」的**，不能做子类型向上转换；**只读容器（`Sequence`）是「协变（covariant）」的**，允许向上转换。

```python
# ❌ 报错：list[ToolResult] 不能赋给 list[ContentItem]（即使 ToolResult 是 ContentItem 子类型）
content: list[ContentItem] = results  # results 是 list[ToolResult]

# ✅ 正确：Sequence 只读，允许协变
content: Sequence[ContentItem] = results
```

项目在 `types.py` 的 `Event.content` 上使用了 `Sequence[ContentItem]`：

```python
class Event(BaseModel):
    content: Sequence[ContentItem] = Field(default_factory=list)
```

> 教学提示：这是理解 Python 泛型类型安全的关键概念——「可变容器不变、只读容器协变」。
> 经验法则：**除非确实需要可变，否则优先用 `Sequence` 而非 `list`**。

### 2.6 第三方类型（`np.ndarray`）

第三方库的类型直接使用其提供的类型对象，如 `numpy` 的 `np.ndarray`：

```python
def get_embeddings(...) -> np.ndarray:
    ...
```

> 注意：返回类型要「诚实」反映真实返回。`get_embeddings` 内部用
> `np.array(...)` 构造，因此标注 `np.ndarray` 而非 `list[float]`。

---

## 3. 导入与延迟求值约定

### 3.1 `from __future__ import annotations`

`from __future__ import annotations` 的作用是让类型注解**延迟求值**（注解被当作字符串保存），从而解决两类问题：

1. **跨模块循环导入**：注解引用了另一个模块的类，而那个模块又（直接或间接）导回本模块，运行时求值会触发 `NameError` 或导入错误。
2. **前向引用**：注解引用了同文件里「后面才定义」的类。

```python
from __future__ import annotations
```

> **项目采用「按需启用」策略，而非全量统一**：
>
> - **仅在**使用 `TYPE_CHECKING` 延迟导入的文件中启用——因为这类文件在注解里
>   引用了「仅在类型检查时导入、运行时不存在」的名字（如 `Agent`），必须靠
>   `from __future__ import annotations` 让注解变成字符串，否则运行时会 `NameError`。
> - 其余文件的注解引用的都是**运行时已真实导入**的名字，注解可正常求值，
>   **无需**添加该声明（添加也只是冗余，不改变任何行为）。
>
> 因此，**一个文件是否出现 `from __future__ import annotations`，本身就构成一个
> 明确信号：该文件存在延迟导入 / 循环依赖处理。** 项目当前启用该声明的文件
> 恰好就是全部 4 个使用了 `TYPE_CHECKING` 的模块，规则完全自洽，无遗漏、无冗余。

### 3.2 `TYPE_CHECKING` 延迟导入

仅在**类型注解需要引用、但运行时会产生循环导入**时，使用 `TYPE_CHECKING` 把导入放进「仅供类型检查」的分支：

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..agent import Agent   # 仅类型检查时导入，避免运行时循环依赖
```

项目中用于 `memory/_context_optimizer.py`、`orchestration/_transfer.py`、`tools/_base.py`、`tools/_memory_tool.py` 等需要引用 `Agent` 但又不愿在运行时导入的模块。

> **配套规则**：任何使用了 `TYPE_CHECKING` 延迟导入的文件，**必须同时**在文件顶部
> 声明 `from __future__ import annotations`（见 §3.1）——否则 `if TYPE_CHECKING:`
> 分支里导入的名字在运行时注解求值时会触发 `NameError`。这两个声明是「绑定关系」。

---

## 4. 模块与包命名约定

### 4.1 下划线前缀 = 模块私有

- 单下划线前缀（`_client.py`、`_base.py`、`_helpers.py`）表示**「模块是内部实现，不应被外部直接导入」**。
- 但**包层面**可以通过 `__init__.py` **选择性公开**其中的符号，这是 numpy、pandas 等成熟库的通行做法。

```python
# llm/__init__.py —— 把 _client.py 里的类公开导出
from ._client import LlmClient
```

### 4.2 无下划线 = 可公开模块

`rag.py`、`skills.py`、`config.py`、`agent.py`、`context.py`、`types.py` 等**无下划线前缀**的模块，其符号在顶层 `__init__.py` 中公开导出。

> 命名边界的历史：`_rag.py`、`_skills.py` 曾以下划线前缀存在，但因其功能被
> `agent.py`、`_callbacks.py` 等多处**实际调用**，并非「纯内部实现」，故重命名为
> `rag.py`、`skills.py` 并正式公开导出。这体现了「私有 vs 公开」应依据**实际使用范围**而非字面前缀。

### 4.3 顶层 `__init__.py` 的导出规范

顶层 `__init__.py` 通过 `__all__` 声明公开 API，且 **`__all__` 必须与实际导入的符号保持一致**：

```python
from .rag import get_embeddings, fixed_length_chunking, vector_search
from .skills import SkillInfo, discover_skills, ...
from .config import load_project_env

__all__ = [
    "LlmClient", "Message", "ToolCall", "ToolResult", ...,
    "get_embeddings", "fixed_length_chunking", "vector_search", ...,
]
```

**核心要求**：`__all__` 中的每个符号都必须能通过 `getattr(scratchagent, name)` 访问，且 `from scratchagent import *` 导入的符号集合与 `__all__` 完全一致。

---

## 5. 外部使用方式

项目采用 **src-layout**（源码在 `src/scratchagent/`），安装后通过包名导入：

```python
# 顶层公开 API
from scratchagent import Agent

# 二级模块的类
from scratchagent.llm import LlmClient

# RAG / 技能 / 环境加载
from scratchagent import vector_search, discover_skills, load_project_env
```

---

## 6. 类型检查工具配置

类型检查统一使用 **mypy**（`pyproject.toml` 的 `[tool.mypy]` 段）：

| 开关 | 值 | 说明 |
|------|-----|------|
| `disallow_untyped_defs` | `false` | **教学宽容档**：允许函数暂不标注，避免初学者被海量报错劝退 |
| `check_untyped_defs` | 默认 | 已标注的函数内部仍需自洽 |
| `warn_unreachable` | `true` | 暴露死代码（不可达分支） |
| `warn_unused_ignores` | `false` | 已关闭，避免误报 |
| `warn_return_any` | `true` | 提示返回 `Any` 的函数 |
| `show_error_codes` | `true` | 显示 PEP 错误码，便于自查 |
| `ignore_missing_imports` | `true` | 容忍部分第三方库缺 stub |

运行方式：

```bash
uv run --extra dev mypy src/        # 或 poe mypy
```

---

## 7. 补充约定（常见陷阱）

1. **类型注解用 `:`，赋值用 `=`**，二者不可混淆：
   ```python
   results: list[SearchResult] = []   # ✅ 冒号做注解，等号做赋值
   # results = list[SearchResult] = []  # ❌ 链式赋值，语法错误
   ```

2. **类型精确化的「连锁效应」**：把返回类型从裸 `list` 精确化为 `list[SearchResult]`（或引入 `TypedDict`）后，**下游调用方**的变量类型可能随之暴露不精确之处。这是类型系统「照妖镜」作用的正常表现——发现即修复，而非回避。

3. **生成器里的 `isinstance` 收窄对 mypy 不可见**：若需要收窄类型，应使用**显式变量承接**，而非在生成器表达式中内联判断：
   ```python
   # ❌ mypy 无法据此收窄外层变量的类型
   web_text = "\n".join(... for item in original_content if isinstance(item, Mapping))

   # ✅ 先过滤到独立变量，mypy 能确认其类型
   web_items = [item for item in original_content if isinstance(item, Mapping)]
   web_text = "\n".join(... for item in web_items)
   ```
