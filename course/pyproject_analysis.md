# pyproject.toml 解析（从开发角度）

> 解析对象：`D:\00_persist\agent-from-scratch\pyproject.toml`
> 定位：现代 Python 项目配置，符合 PEP 517/518 标准，Hatchling 构建后端，教学项目。

## 概览

这是一个**结构规范、思路清晰的现代 Python 项目配置**。作为教学项目，它做得好的地方：

- **统一入口**：构建、依赖、类型检查、格式化、测试、任务脚本全部收敛到一个文件，新人克隆后一条命令就能跑起来。
- **依赖版本策略合理**：用 `>=` 下限 + 少数 `~=` 精确锁定（如 `tabulate~=0.9`），符合教学项目「宽松但不失控」。
- **测试配置专业**：pytest 的 marker 区分 e2e/slow、`asyncio_mode=auto`，考虑到了「哪些测试要联网、哪些要 API key」的现实问题。

---

## 1. `[build-system]` — 如何构建这个包

```toml
requires = ["hatchling"]
build-backend = "hatchling.build"
```

- 声明**构建项目本身需要什么工具**（和运行时依赖是两回事）。`requires` 里只有 `hatchling`，意思是「构建时先把 hatchling 装进隔离环境」。
- `build-backend` 指定用 Hatchling 而不是 setuptools/poetry。Hatchling 是现代的、配置极简的构建后端，最大好处是「约定优于配置」——不用写 `setup.py` 或 `MANIFEST.in`，会自动发现包结构。

> 教学价值：让读者看到「现代 Python 打包已经不需要手写 setup.py」。

---

## 2. `[project]` — 包的元数据（核心）

这是 PEP 621 标准的项目元数据，替代旧的 `setup.py` 参数：

| 字段 | 值 | 说明 |
|---|---|---|
| `name` | `scratchagent` | 包名 = 导入名，`import scratchagent` 对应 |
| `version` | `0.1.0` | 语义化版本，初始版 |
| `description` | "A minimal AI Agent from scratch for educational purposes" | 一句话定位：教学用途的最小 Agent |
| `readme` | `README.md` | 发布到 PyPI 时作为项目主页 |
| `license` | `MIT` | 与仓库 LICENSE 一致 |
| `requires-python` | `>=3.13.0, <3.14` | 见下方重点分析 |
| `authors` | YouliangXia | 作者署名（真名拼音 + 邮箱） |
| `keywords` | agents/scratch-agent/ai/llm/educational | PyPI 搜索关键词 |

### 重点：`requires-python = ">=3.13.0, <3.14"`

含义：**这个包只能在 Python 3.13 上安装，3.12 不行，3.14 也不行**（3.14 还没出，但 `<3.14` 提前锁死了上限）。

从开发角度看，这个限制**偏严格**，对教学项目的「易用性」是隐患：

- **问题 1**：很多人（尤其新手）默认装的还是 Python 3.11/3.12，`pip install` 会直接报错，把人挡在门外。
- **问题 2**：`<3.14` 上限其实没必要。3.13 的代码通常能兼容 3.14，提前锁死等于「等 3.14 发布后这包又装不上」。

**建议**：教学项目更适合写成 `>=3.10` 或 `>=3.11`（放宽下限）；若确实用了 3.13 独有特性，就写 `>=3.13` 但**去掉 `<3.14`**。取决于代码是否用到 3.13 专属语法。

---

## 3. `dependencies` — 运行时依赖（16 个）

项目「能跑起来」需要装的东西，按功能分组：

| 分组 | 包 | 作用 |
|---|---|---|
| 环境配置 | `python-dotenv` | 读 `.env` 文件，管理 API key |
| 数据模型 | `pydantic` | Agent 消息、工具调用、配置等数据结构的类型校验 |
| LLM 调用 | `openai`、`litellm` | 前者直连 OpenAI；后者是「统一多模型接口层」，切换不同厂商模型 |
| MCP | `fastmcp`、`mcp[cli]` | MCP 协议实现（对应 `_fast_mcp.py`） |
| 搜索 | `tavily-python` | Tavily 联网搜索（search_compressor_agent 用） |
| 向量检索/RAG | `faiss-cpu`、`chromadb`、`scikit-learn`、`tiktoken` | FAISS + Chroma 两个向量库、embedding、token 计数 |
| 文档处理 | `pymupdf` | 读 PDF（RAG 文档分块、PDF 合并 skill 用） |
| 沙箱执行 | `e2b-code-interpreter` | E2B 云端沙箱（e2b_agent 用） |
| 数值/表格 | `numpy`、`pandas`、`tabulate` | 数据分析示例、表格渲染 |

值得点出的开发细节：

- **`faiss-cpu` 而不是 `faiss`**：`faiss` 默认带 GPU 版会拉一堆 CUDA 依赖，教学项目用 CPU 版避免装包地狱——务实选择。
- **`tabulate~=0.9`**：用 `~=`（兼容版本约束）单独锁定这个包，大概率是 tabulate 0.10 改了输出格式/API，作者踩过坑才锁住。
- **依赖版本下限都很新**（`pandas>=3.0.5`、`numpy>=2.5.0`、`openai>=2.46.0`），说明项目是 2025 底/2026 初维护，紧跟最新版本。

---

## 4. `[project.optional-dependencies]` — 可选依赖组

「按需安装」的依赖分组，用 `pip install scratchagent[dev]` 语法选择性安装：

| 组名 | 内容 | 用途 |
|---|---|---|
| `notebooks` | `jupyterlab` | 教学用，跑 Jupyter 笔记本 |
| `dev` | pytest、mypy、black、isort、poethepoet 等 | 开发者工具链（测试+类型+格式化+任务） |
| `anthropic` | `anthropic` | 支持 Claude 模型（通过 litellm 调用时需要） |
| `examples` | `matplotlib` | 跑 examples 里的绘图示例 |

设计很干净——把「教学使用」和「开发贡献」的依赖分开。

---

## 5. `[project.urls]` — 项目链接

Homepage / Documentation / Repository 三个都指向 GitHub 仓库，显示在 PyPI 项目页侧边栏。

**注意**：Documentation 目前指向 README 的 `#readme` 锚点，以后有独立文档站可改。

---

## 6. `[tool.mypy]` — 类型检查配置

```toml
python_version = "3.13"
warn_return_any = true       # 函数返回 Any 时警告
warn_unused_configs = true   # 检查未使用的配置
strict_equality = true       # 禁止 == 比较不兼容类型
disallow_untyped_defs = false  # 不强制所有函数写类型注解
ignore_missing_imports = true  # 缺 stub 的第三方库不报错
```

体现务实分寸：开启很多「警告」选项，但**没开 `strict = true`**，也没强制 `disallow_untyped_defs`。对教学项目正确——开 `strict` 会大量报错劝退贡献者。

---

## 7. `[tool.black]` / `[tool.isort]` — 代码格式化

```toml
[tool.black]
line-length = 88          # 一行最长 88 字符（black 硬性约定）
target-version = ['py313']

[tool.isort]
profile = "black"         # isort 兼容 black 的 import 排序
line_length = 88
```

- `line-length = 88` 是 Black 社区经典约定（「80 太窄、100 太宽」的折中）。
- `profile = "black"` 是关键：isort 和 black 默认对 import 换行格式有冲突，设置此 profile 让两者一致，避免「格式化打架」。

---

## 8. `[tool.pytest.ini_options]` — 测试配置

```toml
pythonpath = ["src"]           # 让测试能 import 到 src/ 下的包
testpaths = ["tests"]          # 测试目录
addopts = "-v --tb=short --strict-markers"
markers = [
    "e2e: ... (requires network + API keys, deselect by default)",
    "slow: marks tests as slow (>5s)",
]
asyncio_mode = "auto"          # pytest-asyncio 自动处理 async 测试
```

亮点：

- **`pythonpath = ["src"]`**：说明项目用 **src 布局**（代码在 `src/scratchagent/` 下），现代 Python 打包最佳实践——避免「测试导入的是本地代码还是已安装的包」的混淆。
- **`markers` 定义 `e2e` 和 `slow`**：明确区分「要联网/要 API key 的端到端测试」和「慢测试」，配合 `--strict-markers` 防拼错。背后是「CI 里不能跑需要 API key 的测试」的实际痛点。
- **`asyncio_mode = "auto"`**：Agent 框架大量用 `async`，此配置让 `async def test_xxx()` 自动被 asyncio 运行，不用每个测试都写 `@pytest.mark.asyncio`。

---

## 9. `[tool.poe.tasks]` — 任务快捷命令（poethepoet）

用 `poe` 把常用命令定义成别名：

```
poe mypy         →  mypy src/
poe test         →  pytest tests/ -v
poe test-cov     →  pytest tests/ --cov=src/scratchagent --cov-report=term-missing
poe format-black →  black src/ examples/ tests/
```

这是**替代 Makefile 的现代方案**。开发者不用记长命令，直接 `poe test-cov`。对教学项目友好——README 里写「跑 `poe test` 即可」，降低上手门槛。

---

## 总结：这份配置给的信号

1. **成熟度高**：src 布局、PEP 621、Hatchling、可选依赖分组、pytest marker 区分、poe 任务——都是 2024-2026 年 Python 项目最佳实践，不是随便写的。
2. **教学定位清晰**：`description`、`keywords`、`notebooks`/`examples` 可选组，都在强调「教育用途、低门槛」。
3. **两个可优化点**：
   - `requires-python` 的 `>=3.13,<3.14` 偏严，建议放宽（去掉 `<3.14`，下限视代码实际用到的特性决定）。
   - `description` 目前只有一句话，若发 PyPI 可写得更充实。

---

## 后续可选动作

1. 扫源码确认是否用到 3.13 专属语法，给出 `requires-python` 的准确建议。
2. 补 `[tool.hatch.build]` 配置（若有数据文件如 `sales_data.xlsx` 需要随包分发，目前未看到对非 `.py` 文件的打包声明）。
