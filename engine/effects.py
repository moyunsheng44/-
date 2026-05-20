from __future__ import annotations

from models.card import SpellCard, UnitCard
from models.player import Player
from utils.display import effect_label


def resolve_spell(
    card: SpellCard,
    caster: Player,
    opponent: Player,
    target: str | None,
) -> str:
    if card.effect_type == "draw":
        return _apply_draw(card, caster)
    if card.effect_type == "damage":
        return _apply_damage(card, caster, opponent, target)
    if card.effect_type == "heal":
        return _apply_heal(card, caster, opponent, target)
    if card.effect_type == "gain_mana":
        return _apply_gain_mana(card, caster)
    raise ValueError(f"不支持的法术效果：{effect_label(card.effect_type)}")


def _apply_draw(card: SpellCard, caster: Player) -> str:
    drawn_cards: list[str] = []
    overdraw_count = 0
    for _ in range(card.effect_value):
        drawn = caster.draw_card()
        if drawn is None:
            break
        if drawn == "overdraw":
            overdraw_count += 1
            continue
        drawn_cards.append(drawn.name)
    parts: list[str] = []
    if drawn_cards:
        parts.append(f"抽到了：{', '.join(drawn_cards)}")
    if overdraw_count:
        parts.append(f"手牌已满，{overdraw_count} 张牌被弃置（爆牌）")
    if not parts:
        return f"{caster.name} 使用了【{card.name}】，但牌库已经空了。"
    return f"{caster.name} 使用了【{card.name}】，" + "；".join(parts) + "。"


def _apply_damage(
    card: SpellCard,
    caster: Player,
    opponent: Player,
    target: str | None,
) -> str:
    if card.target_type == "enemy_player":
        opponent.take_damage(card.effect_value)
        return (
            f"{caster.name} 使用了【{card.name}】，对 {opponent.name} 造成了 "
            f"{card.effect_value} 点伤害。"
        )
    if card.target_type == "enemy_unit":
        unit = _require_enemy_unit(opponent, target)
        unit.health -= card.effect_value
        return (
            f"{caster.name} 使用了【{card.name}】，对 {unit.name} 造成了 "
            f"{card.effect_value} 点伤害。"
        )
    raise ValueError("伤害法术的目标类型无效。")


def _apply_heal(
    card: SpellCard,
    caster: Player,
    opponent: Player,
    target: str | None,
) -> str:
    if card.target_type == "ally_player":
        caster.heal(card.effect_value)
        return (
            f"{caster.name} 使用了【{card.name}】，恢复了 "
            f"{card.effect_value} 点生命。"
        )
    if card.target_type == "ally_unit":
        unit = _require_friendly_unit(caster, target)
        unit.health = min(unit.max_health, unit.health + card.effect_value)
        return (
            f"{caster.name} 使用了【{card.name}】，为 "
            f"{unit.name} 恢复了 {card.effect_value} 点生命。"
        )
    raise ValueError("治疗法术的目标类型无效。")


def _apply_gain_mana(card: SpellCard, caster: Player) -> str:
    caster.max_mana += card.effect_value
    return f"{caster.name} 使用了【{card.name}】，费用上限 +{card.effect_value}（当前费用不变）。"


def _require_enemy_unit(opponent: Player, target: str | None) -> UnitCard:
    if target is None:
        raise ValueError("这个法术需要选择一个敌方单位作为目标。")
    index = _parse_index(target)
    try:
        return opponent.board[index]
    except IndexError as error:
        raise ValueError("敌方单位目标超出范围。") from error


def _require_friendly_unit(caster: Player, target: str | None) -> UnitCard:
    if target is None:
        raise ValueError("这个法术需要选择一个我方单位作为目标。")
    index = _parse_index(target)
    try:
        return caster.board[index]
    except IndexError as error:
        raise ValueError("我方单位目标超出范围。") from error


def _parse_index(raw_value: str) -> int:
    try:
        return int(raw_value)
    except ValueError as error:
        raise ValueError("目标编号必须是数字。") from error
