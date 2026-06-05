# 更新日志

## v1.4.4

- 移除 MC 消息对 `activated_handlers` 的跳过判断，避免上下文记录类插件导致 LLM 工具不执行。
- 增强热重载清理：新实例启动时主动断开旧 MCDR 桥接客户端并取消旧监听任务。
- 使用跨模块全局去重缓存，降低热重载期间重复 MC 消息提交概率。

## v1.4.3

- 修复 AstrBot 内置 `main_handle_empty_mention` 被误判为其它插件指令的问题。
- 修复插件热重载后 MCDR 监听任务可能残留，导致同一条 MC 消息重复提交的问题。
- 增加短时间重复 MC 聊天事件去重。

## v1.4.2

- 修复 MC 消息被误判为命中 AstrBot 内置 Agent 指令，导致插件 LLM 工具上下文异常的问题。

## v1.4.1

- 修复部分 AstrBot 版本不支持 `_conf_schema.json` 中 `dict` 类型导致插件加载失败的问题。
- `player_aliases` 改为兼容性更好的 JSON 文本配置。

## v1.4.0

- 新增玩家别名功能。
- 改为 MCDR 桥接模式。
