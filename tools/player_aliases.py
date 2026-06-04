"""
Player alias resolver.

Config format:
{
    "doubiev": ["豆包", "小豆", "dbv"]
}
"""

from typing import Any


_player_aliases: dict[str, list[str]] = {}
_alias_to_player: dict[str, str] = {}


def set_player_aliases(aliases: Any):
    """Set player aliases from plugin config."""
    global _player_aliases, _alias_to_player

    normalized = _normalize_alias_config(aliases)
    _player_aliases = normalized
    _alias_to_player = {}

    for player, alias_list in normalized.items():
        _alias_to_player[player.lower()] = player
        for alias in alias_list:
            _alias_to_player[alias.lower()] = player


def get_player_aliases() -> dict[str, list[str]]:
    """Return current alias mapping."""
    return {player: aliases[:] for player, aliases in _player_aliases.items()}


def resolve_player_name(name: str) -> str:
    """
    Resolve an exact player name or alias to the real Minecraft player id.

    Selectors and coordinate-like targets are intentionally left unchanged.
    """
    if not isinstance(name, str):
        return name

    stripped = name.strip()
    if not stripped or stripped.startswith("@") or " " in stripped:
        return name

    return _alias_to_player.get(stripped.lower(), stripped)


def resolve_command_aliases(command: str) -> str:
    """
    Replace exact command tokens that match aliases.

    This is intentionally conservative: quoted text and punctuation-heavy tokens
    are not rewritten, so arbitrary commands remain predictable.
    """
    if not isinstance(command, str) or not command:
        return command

    tokens = command.split(" ")
    resolved_tokens = []
    for token in tokens:
        resolved_tokens.append(resolve_player_name(token))
    return " ".join(resolved_tokens)


def format_player_aliases() -> str:
    """Return a human-readable alias list."""
    if not _player_aliases:
        return "当前未配置玩家别名"

    lines = ["玩家别名列表:"]
    for player, aliases in sorted(_player_aliases.items()):
        alias_text = "、".join(aliases) if aliases else "无"
        lines.append(f"- {player}: {alias_text}")
    return "\n".join(lines)


async def list_player_aliases() -> str:
    """列出当前配置的MC玩家别名"""
    return format_player_aliases()


def _normalize_alias_config(aliases: Any) -> dict[str, list[str]]:
    if not aliases:
        return {}

    if isinstance(aliases, dict):
        items = aliases.items()
    elif isinstance(aliases, list):
        items = []
        for entry in aliases:
            if isinstance(entry, dict):
                player = entry.get("player") or entry.get("id") or entry.get("name")
                alias_list = entry.get("aliases") or entry.get("alias") or []
                items.append((player, alias_list))
    else:
        return {}

    normalized: dict[str, list[str]] = {}
    for player, alias_list in items:
        if not isinstance(player, str) or not player.strip():
            continue

        if isinstance(alias_list, str):
            alias_values = [alias_list]
        elif isinstance(alias_list, list):
            alias_values = alias_list
        else:
            continue

        player_id = player.strip()
        clean_aliases = []
        seen = set()
        for alias in alias_values:
            if not isinstance(alias, str):
                continue
            clean_alias = alias.strip()
            if not clean_alias or clean_alias.lower() in seen:
                continue
            clean_aliases.append(clean_alias)
            seen.add(clean_alias.lower())

        normalized[player_id] = clean_aliases

    return normalized
