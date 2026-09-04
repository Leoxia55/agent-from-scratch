# 错误说明

| 错误/状态 | 常见原因 | 处理方式 |
| --- | --- | --- |
| `LLMConfigError` | provider 缺少 key/base URL | 检查对应环境变量和 `.env` 路径 |
| `UnsupportedProviderError` | provider 字符串未知 | 使用 `Provider` 的四个值 |
| `E2BSandboxConfigurationError` | E2B key、模板、timeout 或 SDK 失败 | 检查 `E2B_*`，确认 timeout > 0 |
| `AgentResult.status == "pending"` | 工具需要人工确认 | 传回匹配的 `ToolConfirmation` |
| `ToolResult.status == "error"` | 工具不存在、参数 JSON 无效或执行异常 | 查看 `content`，修正 schema/输入 |
| `RuntimeError` from `LlmClient.ask` | `generate()` 返回 error | 先记录 `LlmResponse.error_message` |
| 达到 `max_steps` | 模型持续调用工具或无法收敛 | 增加明确终止指令或调整上限 |

## 源码注意事项

当前源码的 `Agent.run()` 最终返回分支构造 `AgentResult` 时没有显式传入 `status`，而 `AgentResult` 定义要求该字段。若普通成功执行出现 `TypeError`（缺少 `status`），这是实现缺口，不是 provider 响应错误；修复源码为 `status="complete"` 后再运行教程示例。

此外，固定长度切块没有运行时校验 `overlap < chunk_size`；调用方应主动保证该约束，避免循环不前进。文件解压工具也未替调用方防范路径穿越，处理不可信压缩包前必须增加目标路径校验。

当前 `ParallelWorkFlow` 和部分工作流结束分支也直接构造 `AgentResult` 而未显式传入 `status`；若工作流成功路径出现同类 `TypeError`，应在源码中补上 `status="complete"`，再依照[工作流参考](workflow.md)使用。
