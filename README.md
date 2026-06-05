# AstrBot MCDR服务器管理插件

通过LLM智能管理Minecraft服务器的AstrBot插件。现在通过 MCDR 桥接插件与服务器联动，不再需要 AstrBot 直接连接 MC 原生 RCON，也不需要在 MC 服务器侧运行额外的聊天日志截获脚本。

## ✨ 功能特性

- 🤖 **自然语言交互**：无需命令前缀，直接与LLM对话即可管理服务器
- 🎮 **全面管理**：支持玩家管理、游戏操作、服务器管理、世界操作等功能
- 🏷️ **玩家别名**：支持为一个MC游戏ID配置多个别名，LLM工具会自动解析
- 🔒 **权限控制**：支持管理员白名单，确保服务器安全
- 🌐 **MCDR联动**：通过 MCDR 插件接收聊天/事件并代发服务器命令

## 📦 安装

### 方法一：通过AstrBot插件市场安装（推荐）

1. 打开AstrBot管理面板
2. 进入「插件管理」
3. 搜索 `astrbot_plugin_mcdr_manager`
4. 点击安装

### 方法二：手动安装

1. 下载本插件到 AstrBot 的 `data/plugins/` 目录
2. 重启 AstrBot

## ⚙️ 配置

### 1. 安装MCDR桥接插件

本仓库只包含 AstrBot 插件代码。配套的 MCDR 桥接插件请单独放在 MCDR 的插件目录中，不要放进 AstrBot 插件目录。放好后在 MCDR 控制台执行：

```text
!!MCDR reload plugin
```

首次加载后，MCDR 会生成配置文件 `config/astrbot_mc_bridge/config.json`：

```json
{
  "host": "127.0.0.1",
  "port": 25576,
  "token": "",
  "heartbeat_interval": 10,
  "client_timeout": 30,
  "use_rcon_query": true,
  "command_timeout": 8
}
```

如果 AstrBot 与 MCDR 不在同一台机器，把 `host` 改为 `0.0.0.0`，并建议设置 `token`。

### 2. 插件配置

在AstrBot管理面板中配置本插件：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `mcdr_host` | MCDR桥接插件地址 | `127.0.0.1` |
| `mcdr_port` | MCDR桥接插件端口 | `25576` |
| `mcdr_token` | MCDR桥接Token，需与MCDR插件配置一致 | `""` |
| `mcdr_reconnect_interval` | MCDR桥接重连间隔 | `10` |
| `mcdr_max_reconnect_attempts` | MCDR桥接最大重连次数，0表示无限 | `0` |
| `mcdr_command_timeout` | 命令等待超时时间 | `10` |
| `admin_ids` | 管理员ID列表（QQ号或MC玩家名） | `[]`（空表示所有人可用） |
| `player_aliases` | 玩家别名JSON文本，真实游戏ID对应多个别名 | `{}` |
| `enable_dangerous_commands` | 启用危险命令（如stop） | `false` |
| `enable_chat_response` | 将LLM响应发送回MC聊天框 | `true` |
| `bot_nickname` | 在MC中显示的机器人昵称 | `"Bot"` |
| `enable_unified_context` | 启用MC和QQ群的统一上下文 | `false` |
| `unified_group_umo` | 统一上下文目标群UMO | `""` |
| `mc_message_prefix` | MC消息在统一上下文中的前缀 | `"[MC]"` |

配置示例：
```json
{
  "mcdr_host": "127.0.0.1",
  "mcdr_port": 25576,
  "mcdr_token": "",
  "admin_ids": ["123456789", "Steve", "Alex"],
  "player_aliases": "{\"doubiev\": [\"豆包\", \"小豆\", \"豆比\"], \"Steve\": [\"史蒂夫\"]}",
  "enable_dangerous_commands": false,
  "enable_chat_response": true,
  "bot_nickname": "MC助手",
  "enable_unified_context": false,
  "unified_group_umo": "",
  "mc_message_prefix": "[MC]"
}
```

### 玩家别名

`player_aliases` 是一段JSON文本，用真实 MC 游戏ID作为键，值为该玩家的别名列表。配置后，玩家相关工具会自动把别名解析为真实游戏ID。

例如玩家游戏ID为 `doubiev`：

```json
{
  "doubiev": ["豆包", "小豆", "豆比"]
}
```

之后可以直接说：

```text
把豆包传送到Alex旁边
给小豆64个钻石
把豆比切成创造模式
```

这些请求会自动按 `doubiev` 执行。支持别名解析的工具包括玩家管理、物品给予、传送、游戏模式、清背包、经验、`tellraw/title` 的目标玩家，以及 `execute_command` 中按空格分隔的简单玩家名 token。可以询问“列出玩家别名”让机器人调用 `list_player_aliases` 查看当前配置。

### 3. MC游戏内聊天支持

安装并连接 MCDR 桥接插件后，可以在MC游戏内直接与机器人对话：

1. **配置权限**：
   - `admin_ids` 中添加MC玩家名即可授予权限(你游戏名是啥就填啥)
   - 例如：`"admin_ids": ["Steve", "Alex"]` 允许这两个MC玩家执行管理命令
   - 格式：MC玩家的user_id为 `mc_player_{玩家名}`

2. **在MC中使用**：
   - 所有MC聊天消息都会提交到AstrBot，LLM会看到完整的聊天上下文
   - 唤醒词在AstrBot的 `wake_prefix` 配置中统一管理（如 `"wake_prefix": ["小面包"]`）
   - 只有包含唤醒词的消息才会触发LLM回复
   - 示例：发送 `小面包 查看在线玩家`，机器人会自动回复到MC聊天框

**权限校验说明**：
- QQ消息：使用QQ号校验（如 `"123456789"`）
- MC消息：使用玩家名校验（如 `"Steve"`）
- 系统会自动识别消息来源并应用对应的权限规则

### 4. 统一会话上下文（高级功能）

启用后，MC游戏内聊天和指定QQ群可以共享同一个对话上下文，实现跨平台无缝交流。

**功能特性**：
- 🔗 **统一上下文**：MC玩家和QQ群成员在同一对话中交流
- 🤖 **双向感知**：LLM能同时看到MC和QQ的消息历史
- 🎯 **定向推送**：支持将MC事件推送到指定QQ群
- 🛠️ **工具支持**：提供 `send_to_qq_group` 工具，让LLM主动向QQ群发送消息

**配置步骤**：

1. **获取QQ群UMO**：
   - 在目标QQ群中发送任意消息
   - 在AstrBot后台日志中查找类似 `aiocqhttp_default:GroupMessage:123456789` 的UMO字符串
   - 格式说明：`平台ID:消息类型:群号`

2. **启用统一上下文**：
   ```json
   {
     "enable_unified_context": true,
     "unified_group_umo": "aiocqhttp_default:GroupMessage:123456789",
     "mc_message_prefix": "[MC]"
   }
   ```

3. **工作原理**：
   - 所有MC聊天消息会自动提交到AstrBot的指定QQ群会话
   - MC消息会带有发送者昵称（如 `Steve(MC)`）
   - LLM能看到完整的MC和QQ混合对话历史
   - MC系统事件（登入、登出、成就、死亡）也会记录到会话上下文
   - LLM可使用 `send_to_qq_group` 工具主动向QQ群发送消息

**使用示例**：

```
[QQ群] 用户A: @Bot 服务器现在有多少人在线？
[MC] Steve: 有3个人，但是Alex好像挂机了
[QQ群] Bot: 当前在线3人：Steve、Alex、Notch。根据Steve的反馈，Alex可能在挂机。
[MC] Alex: 我没挂机！我在挖矿呢
[QQ群] Bot: 好的，Alex说他在挖矿，并没有挂机。
```

**注意事项**：
- 统一上下文需要 MCDR 桥接连接正常
- `unified_group_umo` 必须填写正确的UMO格式
- MC消息前缀可自定义，用于在QQ群中区分消息来源
- 所有MC消息都会提交到指定QQ群的会话上下文，由AstrBot的 `wake_prefix` 控制是否唤醒LLM

## 📖 使用方法

**无需命令前缀！** 直接与AstrBot对话即可管理服务器。

### 使用示例

```
用户: 查看在线玩家
Bot: 在线玩家: There are 3 of a max of 20 players online: Steve, Alex, Notch

用户: 把Steve踢出服务器，原因是挂机太久
Bot: 踢出玩家 Steve: Kicked Steve: 挂机太久

用户: 给Alex 64个钻石
Bot: 给予 Alex 64个 minecraft:diamond: Given [Diamond] x 64 to Alex

用户: 把时间调成白天
Bot: 设置时间为 day: Set the time to 1000

用户: 把天气变成晴天
Bot: 设置天气为 clear: Changed the weather to clear

用户: 封禁Hacker这个玩家
Bot: 封禁玩家 Hacker: Banned Hacker: 违反服务器规则

用户: 把难度调成困难
Bot: 设置难度为 hard: Set game difficulty to Hard

用户: 开启死亡不掉落
Bot: 设置游戏规则 keepInventory = true: Gamerule keepInventory is now set to: true
```

## 🛠️ 支持的功能

### 玩家管理
- ✅ 踢出玩家（kick）🔒
- ✅ 封禁/解封玩家（ban/pardon）🔒
- ✅ 管理OP权限（op/deop）🔒
- ✅ 白名单管理（whitelist add/remove）🔒

### 游戏操作
- ✅ 给予物品（give）🔒
- ✅ 传送玩家（tp）🔒
- ✅ 设置游戏模式（gamemode）🔒
- ✅ 杀死实体（kill）🔒
- ✅ 清空背包（clear）🔒
- ✅ 设置经验（xp）🔒

### 服务器管理
- ✅ 查看在线玩家（list）🆓
- ✅ 服务器广播（say）🔒
- ✅ 格式化消息（tellraw）🔒
- ✅ 屏幕标题（title）🔒
- ✅ 保存世界（save-all）🔒
- ✅ 查看白名单（whitelist list）🆓
- ✅ 查看封禁列表（banlist）🆓
- ✅ 执行自定义命令（execute_command）🔒
- ✅ 查看玩家别名（list_player_aliases）🆓
- ⚠️ 停止服务器（stop）🔒 - 需启用危险命令

### 世界操作
- ✅ 设置天气（weather）🔒
- ✅ 设置时间（time）🔒
- ✅ 设置难度（difficulty）🔒
- ✅ 设置游戏规则（gamerule）🔒
- ✅ 生成实体（summon）🔒

### 🆕 脚本执行器
- ✅ 执行Python脚本（execute_script）🔒
- ✅ 列出可用工具（list_script_tools）🆓

### 🔗 统一上下文工具
- ✅ 发送消息到QQ群（send_to_qq_group）🔒
  - 需要启用统一上下文功能
  - 允许LLM主动向配置的QQ群发送消息
  - 可用于向QQ群推送MC服务器事件或状态

**图标说明：**
- 🔒 需要管理员权限
- 🆓 无需权限，所有人可用

## 🎯 脚本执行器

插件内置了强大的脚本执行器，允许LLM编写Python脚本来完成复杂的自动化任务。


### 脚本功能特性

- ✅ **异步执行**：支持 async/await 语法
- ✅ **工具集成**：可调用所有40+个MC管理工具
- ✅ **超时控制**：默认60秒超时，可自定义
- ✅ **错误处理**：完善的异常捕获和错误报告
- ✅ **输出捕获**：自动捕获print输出



## 🔐 权限分级说明

插件的所有工具按照危险程度分为不同等级：

### 🟢 无需权限（只读操作）
以下工具仅查询信息，不会修改服务器状态，**任何用户**都可以使用：

- `list_players` - 查看在线玩家
- `whitelist_list` - 查看白名单
- `banlist` - 查看封禁列表
- `list_script_tools` - 查看可用工具列表

### 🔴 需要权限（管理操作）
所有其他工具都需要管理员权限，包括：

- **玩家管理**：kick、ban、op等
- **游戏操作**：give、tp、gamemode等
- **服务器管理**：save、say、tellraw等
- **世界管理**：weather、time、difficulty等
- **脚本执行**：execute_script

### 权限配置示例

```json
{
  "admin_ids": ["123456789", "Steve", "Alex"]
}
```

- 留空 `[]`：所有人都有权限（**仅用于测试**）
- 添加QQ号：QQ用户权限控制
- 添加玩家名：MC玩家权限控制

##  安全建议

1. **设置桥接Token**：跨机器部署或非本机监听时，请在 MCDR 插件和 AstrBot 插件中配置相同的 `token`
2. **限制管理员**：在 `admin_ids` 中明确指定可以使用的用户
3. **生产环境必须配置管理员列表**：不要留空 `admin_ids`
4. **禁用危险命令**：保持 `enable_dangerous_commands` 为 `false`，除非确实需要
5. **防火墙配置**：如果MCDR和AstrBot不在同一台机器，只放行 MCDR 桥接端口
6. **谨慎使用脚本执行器**：`execute_script` 可以调用任何已注册工具，请仅授予信任用户

## 🔧 故障排除

### 连接失败

**故障排查步骤：**

1. 确认 MCDR 已启动并加载 `astrbot_mc_bridge`
2. 确认 MCDR 插件配置中的 `host` / `port` 与 AstrBot 的 `mcdr_host` / `mcdr_port` 一致
3. 如果配置了 `token`，确认两边完全一致
4. 如果 MCDR 和 AstrBot 在不同机器，确认 MCDR 插件 `host` 不是 `127.0.0.1`，并检查防火墙
5. 在 AstrBot 中使用 `/test_connection` 测试桥接连接

### 命令无响应

1. 检查AstrBot是否正确配置了LLM提供者
2. 检查插件配置是否正确
3. 查看AstrBot日志获取详细错误信息
4. 如果命令没有返回详细输出，在 MCDR 插件配置中保持 `use_rcon_query: true` 并确保 MCDR 自身可用 RCON；否则桥接插件会退回到 `server.execute()`，命令会发出但只能返回“无返回信息”

## 📝 更新日志

### v1.4.3
- 🐛 修复AstrBot内置 `main_handle_empty_mention` 被误判为其它插件指令的问题
- 🐛 修复插件热重载后MCDR监听任务可能残留，导致同一条MC消息重复提交的问题
- 🛡️ 增加短时间重复MC聊天事件去重

### v1.4.2
- 🐛 修复MC消息被误判为命中AstrBot内置Agent指令，导致插件LLM工具上下文异常的问题

### v1.4.1
- 🐛 修复部分 AstrBot 版本不支持 `_conf_schema.json` 中 `dict` 类型导致插件加载失败的问题
  - `player_aliases` 改为兼容性更好的JSON文本配置

### v1.4.0
- ✨ 新增玩家别名功能
  - 支持在 `player_aliases` 中为一个MC游戏ID配置多个别名
  - 玩家相关工具、脚本执行器工具和简单自定义命令会自动解析别名
  - 新增 `list_player_aliases` 工具用于查看当前别名配置

### v1.3.0
- ✨ 改为 MCDR 桥接模式
  - 新增 `mcdr_client.py`，AstrBot 侧通过 TCP 长连接连接 MCDR
  - 新增配套 MCDR 单文件桥接插件，需与 AstrBot 插件分开部署
  - MC聊天、玩家加入/离开、成就、死亡事件由 MCDR 直接推送
  - 服务器命令通过 MCDR 桥接执行，不再要求 AstrBot 直连 MC 原生 RCON

### v1.2.0
- ✨ 新增统一会话上下文功能
  - 支持MC游戏内聊天和QQ群共享对话上下文
  - LLM可同时感知MC和QQ的消息历史
  - 新增 `send_to_qq_group` 工具，LLM可主动向QQ群发送消息
  - MC系统事件（登入、登出、成就、死亡）自动记录到上下文
- 🔧 优化消息处理
  - 改进MC消息提交机制，支持与AstrBot唤醒词无缝集成
  - 过滤Agent多轮调用的中间响应，避免发送无效内容到MC
- 📚 文档完善
  - 添加统一会话上下文配置和使用说明
  - 完善UMO获取和配置步骤

### v1.1.0
- ✨ 新增脚本执行器功能
  - 允许LLM编写Python脚本执行复杂任务
  - 支持异步执行和超时控制
  - 完善的错误处理和输出捕获
- 🔓 权限优化
  - 4个只读工具无需权限：list_players、whitelist_list、banlist、list_script_tools
  - 所有管理操作工具保留权限控制
- 📚 文档完善
  - 添加脚本执行器详细文档
  - 添加权限分级说明

### v1.0.0
- 初始版本
- 支持玩家管理、游戏操作、服务器管理、世界操作
- 支持LLM智能理解自然语言（无需命令前缀）
- 支持管理员权限控制

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 💬 支持

如有问题，请在GitHub仓库提交Issue。
