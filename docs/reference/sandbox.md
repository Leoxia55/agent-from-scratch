# Sandbox 参考

导入：`from scratchagent.sandbox import create_e2b_sandbox, register_sandbox_tools, close_e2b_sandbox`

## 创建与销毁

```python
sandbox = create_e2b_sandbox(
    api_key=None,
    template=None,
    timeout=300,
    allow_internet_access=False,
)
try:
    ...
finally:
    close_e2b_sandbox(sandbox)
```

key 缺失、模板或 timeout 无效时抛出 `E2BSandboxConfigurationError`；底层 SDK 错误也会包装为该异常。默认不允许互联网访问，timeout 必须大于 0。

`register_sandbox_tools(sandbox, tools)` 读取每个 `sandbox_executable` 工具的源代码，在沙箱中注册。Agent 使用 `code_execution="e2b"` 时会自动创建、注册、上传 Skills，并在自己拥有环境时清理。

相关工具：`execute_python_in_e2b(context, code)`、`base_e2b_tool(context, command)`、`upload_file_to_e2b(context, local_path, sandbox_path=None)`。三者都要求 `context.code_env` 已设置。

