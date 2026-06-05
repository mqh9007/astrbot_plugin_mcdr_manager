"""
MCDR bridge client for AstrBot.

The client keeps one TCP connection to the companion MCDR plugin.  It receives
Minecraft chat/events from MCDR and sends Minecraft commands back through the
same bridge.
"""

import asyncio
import json
import time
import uuid
from typing import Callable, Optional

from astrbot.api import logger


class MCDRBridgeClient:
    """Async client for the MCDR bridge plugin."""

    HEARTBEAT_TIMEOUT = 30

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 25576,
        token: str = "",
        reconnect_interval: int = 10,
        max_reconnect_attempts: int = 0,
        command_timeout: int = 10,
    ):
        self.host = host
        self.port = port
        self.token = token
        self.reconnect_interval = reconnect_interval
        self.max_reconnect_attempts = max_reconnect_attempts
        self.command_timeout = command_timeout

        self.reader: Optional[asyncio.StreamReader] = None
        self.writer: Optional[asyncio.StreamWriter] = None
        self.running = False
        self.should_reconnect = True
        self.reconnect_count = 0
        self.last_heartbeat_time = 0.0

        self.on_chat_message: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_reconnect: Optional[Callable] = None
        self.on_player_join: Optional[Callable] = None
        self.on_player_leave: Optional[Callable] = None
        self.on_player_advancement: Optional[Callable] = None
        self.on_player_death: Optional[Callable] = None
        self.fake_event_handler: Optional[Callable] = None

        self._write_lock = asyncio.Lock()
        self._connect_lock = asyncio.Lock()
        self._pending_commands: dict[str, asyncio.Future] = {}
        self._recent_chat_events: dict[tuple[str, str], float] = {}

    async def connect(self) -> bool:
        """Connect to the MCDR bridge."""
        async with self._connect_lock:
            if self.reader and self.writer and not self.writer.is_closing():
                return True

            try:
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=10.0,
                )
                await self._send_json({"type": "auth", "token": self.token})
                self.running = True
                self.last_heartbeat_time = time.time()
                logger.info(f"已连接到MCDR桥接插件: {self.host}:{self.port}")

                if self.reconnect_count > 0:
                    logger.info(f"MCDR桥接重连成功（共尝试 {self.reconnect_count} 次）")
                    self.reconnect_count = 0
                    if self.on_reconnect:
                        await self.on_reconnect()

                return True
            except asyncio.TimeoutError:
                logger.error(f"连接MCDR桥接插件超时: {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"连接MCDR桥接插件失败: {e}")

            self.reader = None
            self.writer = None
            return False

    async def disconnect(self, stop_reconnect: bool = True):
        """Disconnect and optionally stop reconnecting."""
        self.running = False
        if stop_reconnect:
            self.should_reconnect = False

        for future in list(self._pending_commands.values()):
            if not future.done():
                future.set_exception(ConnectionError("MCDR桥接连接已断开"))
        self._pending_commands.clear()

        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
            except Exception:
                pass

        self.reader = None
        self.writer = None
        logger.info("已断开与MCDR桥接插件的连接")

    async def start_listening(self):
        """Listen for events and command responses with auto reconnect."""
        self.should_reconnect = True
        self.reconnect_count = 0

        while self.should_reconnect:
            if not self.reader:
                if not await self.connect():
                    if self.reconnect_interval > 0 and self._should_retry_reconnect():
                        self.reconnect_count += 1
                        logger.info(f"将在 {self.reconnect_interval} 秒后重连MCDR桥接（第 {self.reconnect_count} 次尝试）")
                        await asyncio.sleep(self.reconnect_interval)
                        continue
                    break

            heartbeat_task = asyncio.create_task(self._check_heartbeat())
            try:
                while self.running and self.reader:
                    try:
                        line = await asyncio.wait_for(self.reader.readline(), timeout=1.0)
                    except asyncio.TimeoutError:
                        continue

                    if not line:
                        logger.warning("MCDR桥接连接断开")
                        break

                    try:
                        msg = json.loads(line.decode("utf-8").strip())
                        await self._process_message(msg)
                    except json.JSONDecodeError as e:
                        logger.error(f"MCDR桥接收到非JSON消息: {e}")
                    except Exception as e:
                        logger.error(f"处理MCDR桥接消息时出错: {e}")
            finally:
                heartbeat_task.cancel()
                await self.disconnect(stop_reconnect=False)
                if self.on_disconnect:
                    try:
                        await self.on_disconnect()
                    except Exception as e:
                        logger.error(f"执行MCDR桥接断连回调时出错: {e}")

            if self.should_reconnect and self.reconnect_interval > 0 and self._should_retry_reconnect():
                self.reconnect_count += 1
                logger.info(f"将在 {self.reconnect_interval} 秒后重连MCDR桥接（第 {self.reconnect_count} 次尝试）")
                await asyncio.sleep(self.reconnect_interval)
            else:
                break

        logger.info("MCDR桥接监听已停止")

    async def execute_async(self, command: str) -> str:
        """Execute a Minecraft command via MCDR."""
        if command.startswith("/"):
            command = command[1:]

        if not self.reader or not self.writer or self.writer.is_closing():
            if not await self.connect():
                return f"错误: 无法连接到MCDR桥接插件 {self.host}:{self.port}"

        request_id = uuid.uuid4().hex
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_commands[request_id] = future

        try:
            await self._send_json({
                "type": "command",
                "id": request_id,
                "command": command,
            })
            response = await asyncio.wait_for(future, timeout=self.command_timeout)
            if response.get("success", False):
                return response.get("result") or "命令执行成功（无返回信息）"
            return f"错误: {response.get('error') or 'MCDR桥接执行命令失败'}"
        except asyncio.TimeoutError:
            return f"错误: MCDR桥接执行命令超时（{self.command_timeout}秒）"
        except Exception as e:
            return f"错误: MCDR桥接执行命令时出错: {e}"
        finally:
            self._pending_commands.pop(request_id, None)

    async def test_connection_async(self) -> tuple[bool, str]:
        """Test bridge connection and command path."""
        if not await self.connect():
            return False, f"无法连接到MCDR桥接插件 {self.host}:{self.port}"
        result = await self.execute_async("list")
        if result.startswith("错误:"):
            return False, result
        return True, f"连接成功！{result}"

    async def test_connection(self) -> tuple[bool, str]:
        """Compatibility helper used by the old log test command."""
        return await self.test_connection_async()

    async def close(self):
        await self.disconnect(stop_reconnect=True)

    async def _process_message(self, msg: dict):
        msg_type = msg.get("type")

        if msg_type == "ping":
            self.last_heartbeat_time = time.time()
            await self._send_json({"type": "pong", "timestamp": time.time()})
            return

        if msg_type == "command_result":
            request_id = msg.get("id")
            future = self._pending_commands.get(request_id)
            if future and not future.done():
                future.set_result(msg)
            return

        if msg_type != "event":
            return

        event = msg.get("event")
        player = msg.get("player", "")

        if event == "chat":
            message = msg.get("message", "")
            if self._is_duplicate_chat(player, message):
                logger.debug(f"忽略重复MC聊天事件: <{player}> {message}")
                return

            logger.info(f"[MC聊天] <{player}> {message}")
            if self.fake_event_handler:
                asyncio.create_task(self.fake_event_handler(player, message))
            if self.on_chat_message:
                asyncio.create_task(self.on_chat_message(player, message, ""))
        elif event == "join" and self.on_player_join:
            asyncio.create_task(self.on_player_join(player))
        elif event == "leave" and self.on_player_leave:
            asyncio.create_task(self.on_player_leave(player))
        elif event == "advancement" and self.on_player_advancement:
            asyncio.create_task(self.on_player_advancement(player, msg.get("advancement", "")))
        elif event == "death" and self.on_player_death:
            asyncio.create_task(self.on_player_death(player, msg.get("reason", "")))

    def _is_duplicate_chat(self, player: str, message: str) -> bool:
        now = time.time()
        key = (player, message)

        for old_key, timestamp in list(self._recent_chat_events.items()):
            if now - timestamp > 2:
                self._recent_chat_events.pop(old_key, None)

        last_seen = self._recent_chat_events.get(key)
        self._recent_chat_events[key] = now
        return last_seen is not None and now - last_seen < 2

    async def _send_json(self, payload: dict):
        if not self.writer:
            raise ConnectionError("MCDR桥接未连接")

        data = json.dumps(payload, ensure_ascii=False) + "\n"
        async with self._write_lock:
            self.writer.write(data.encode("utf-8"))
            await self.writer.drain()

    async def _check_heartbeat(self):
        self.last_heartbeat_time = time.time()
        while self.running:
            await asyncio.sleep(5)
            if time.time() - self.last_heartbeat_time > self.HEARTBEAT_TIMEOUT:
                logger.error(f"MCDR桥接心跳超时（超过{self.HEARTBEAT_TIMEOUT}秒），断开连接")
                self.running = False
                break

    def _should_retry_reconnect(self) -> bool:
        return self.max_reconnect_attempts == 0 or self.reconnect_count < self.max_reconnect_attempts

    def set_chat_callback(self, callback: Callable):
        self.on_chat_message = callback

    def set_disconnect_callback(self, callback: Callable):
        self.on_disconnect = callback

    def set_reconnect_callback(self, callback: Callable):
        self.on_reconnect = callback

    def set_player_join_callback(self, callback: Callable):
        self.on_player_join = callback

    def set_player_leave_callback(self, callback: Callable):
        self.on_player_leave = callback

    def set_player_advancement_callback(self, callback: Callable):
        self.on_player_advancement = callback

    def set_player_death_callback(self, callback: Callable):
        self.on_player_death = callback

    def set_fake_event_handler(self, handler: Callable):
        self.fake_event_handler = handler
