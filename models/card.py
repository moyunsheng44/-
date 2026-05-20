from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class CardEffect:
    trigger: str       # "on_deploy" | "on_move" | "on_attack" | "on_death" | "aura"
    effect_type: str   # "damage" | "heal" | "buff_atk" | "buff_hp" | "draw" | "shield"
    value: int
    target: str = "self"  # "self" | "adjacent" | "all_allies" | "random_enemy" | "enemy_hq"
    description: str = ""


@dataclass(slots=True)
class Card:
    id: str
    name: str
    cost: int
    card_type: str


@dataclass(slots=True)
class UnitCard(Card):
    attack: int
    health: int
    unit_class: str = "步兵"
    action_cost: int = 0
    description: str = ""
    emblem: str = "■"
    effects: list[CardEffect] = field(default_factory=list)
    max_health: int = field(init=False)
    can_attack: bool = False
    in_frontline: bool = False
    has_moved_this_turn: bool = False
    has_attacked_this_turn: bool = False

    def __post_init__(self) -> None:
        self.max_health = self.health

    def clone(self) -> "UnitCard":
        return UnitCard(
            id=self.id,
            name=self.name,
            cost=self.cost,
            card_type=self.card_type,
            attack=self.attack,
            health=self.health,
            unit_class=self.unit_class,
            action_cost=self.action_cost,
            description=self.description,
            emblem=self.emblem,
            effects=[CardEffect(e.trigger, e.effect_type, e.value, e.target, e.description)
                      for e in self.effects],
        )

    def describe(self) -> str:
        position = "前线" if self.in_frontline else "后方"
        status = "可攻击" if self.can_attack else "已行动"
        return f"{self.name}（{self.unit_class}，{position}，{self.attack}/{self.health}，{status}）"

    def reset_turn_state(self) -> None:
        self.has_moved_this_turn = False
        self.has_attacked_this_turn = False
        self.can_attack = True


@dataclass(slots=True)
class SpellCard(Card):
    effect_type: str
    effect_value: int
    target_type: Optional[str] = None
    description: str = ""
    emblem: str = "★"

    def clone(self) -> "SpellCard":
        return SpellCard(
            id=self.id,
            name=self.name,
            cost=self.cost,
            card_type=self.card_type,
            effect_type=self.effect_type,
            effect_value=self.effect_value,
            target_type=self.target_type,
            description=self.description,
            emblem=self.emblem,
        )

    def describe(self) -> str:
        target = self.target_type or "none"
        return f"{self.name} [{self.effect_type} {self.effect_value} -> {target}]"
