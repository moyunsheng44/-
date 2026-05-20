from __future__ import annotations

from models.card import SpellCard, UnitCard
from models.player import Player


EFFECT_LABELS = {
    "damage": "伤害",
    "heal": "治疗",
    "draw": "抽牌",
    "gain_mana": "费用槽",
}

TARGET_LABELS = {
    None: "无目标",
    "enemy_player": "敌方总部",
    "enemy_unit": "敌方单位",
    "ally_player": "我方玩家",
    "ally_unit": "我方单位",
}


def describe_card(card: UnitCard | SpellCard) -> str:
    if isinstance(card, UnitCard):
        return f"{card.name} | 单位 | 费用 {card.cost} | 攻击 {card.attack} | 生命 {card.health}"
    return (
        f"{card.name} | 指令 | 费用 {card.cost} | "
        f"{effect_label(card.effect_type)} {card.effect_value} | {target_label(card.target_type)}"
    )


def format_status(current: Player, opponent: Player) -> str:
    return (
        f"{current.name}：生命 {current.health}，费用 {current.mana}/{current.max_mana}，"
        f"牌库 {len(current.deck)}，手牌 {len(current.hand)}\n"
        f"{opponent.name}：生命 {opponent.health}，费用 {opponent.mana}/{opponent.max_mana}，"
        f"牌库 {len(opponent.deck)}，手牌 {len(opponent.hand)}"
    )


def format_board(current: Player, opponent: Player) -> str:
    return (
        f"{current.name} 战场：\n{_format_units(current.board)}\n"
        f"{opponent.name} 战场：\n{_format_units(opponent.board)}"
    )


def _format_units(units: list[UnitCard]) -> str:
    if not units:
        return "  （空）"
    return "\n".join(f"  [{index}] {unit.describe()}" for index, unit in enumerate(units))


def effect_label(effect_type: str) -> str:
    return EFFECT_LABELS.get(effect_type, effect_type)


def target_label(target_type: str | None) -> str:
    return TARGET_LABELS.get(target_type, target_type or "无目标")
