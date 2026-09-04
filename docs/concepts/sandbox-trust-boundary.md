# Sandbox 信任边界

E2B 隔离的是代码执行环境，不是整个 Agent 系统。信任边界如下：

```text
用户/应用 -> 模型 -> Tool schema -> Agent 执行器 -> E2B
                         ^                |
                 不可信参数/输出       文件、网络、凭据权限
```

需要重点区分：

- 模型输出和 RAG 片段是建议，不是授权。
- `required_confirmation` 只暂停指定工具调用，不会限制其他工具或已获得的凭据。
- `base_e2b_tool` 可执行 shell，`upload_file_to_e2b` 可把本地数据带入远端，文件删除/解压工具也有破坏面。
- E2B 的网络开关默认为关闭，但 provider、搜索服务和应用自身仍可能访问外部系统。

生产部署应使用最小工具集合、短超时、资源和预算上限、人工审批、参数白名单、租户隔离、敏感信息脱敏、网络策略和完整审计。不要向 prompt、session、长期 memory 或沙箱上传 API key。

