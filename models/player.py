from __future__ import annotations

import random
from dataclasses import dataclass, field

from models.card import Card, UnitCard


MAX_BACKLINE_UNITS = 4
MAX_FRONTLINE_UNITS = 5
MAX_HAND_SIZE = 10


@dataclass(slots=True)
class Player:
    name: str
    deck: list[Card]
    health: int = 20
    max_mana: int = 0
    mana: int = 0
    hand: list[Card] = field(default_factory=list)
    board: list[UnitCard] = field(default_factory=list)
    discard_pile: list[Card] = field(default_factory=list)
    fatigue: int = 0

    def shuffle_deck(self) -> None:
        random.shuffle(self.deck)

    def draw_card(self) -> Card | None:
        if not self.deck:
            return None
        card = self.deck.pop(0)
        if len(self.hand) >= MAX_HAND_SIZE:
            self.discard_pile.append(card)
            return "overdraw"
        self.hand.append(card)
        return card

    def start_turn(self) -> Card | None:
        self.max_mana = min(self.max_mana + 1, 10)
        self.mana = self.max_mana
        for unit in self.board:
            unit.can_attack = True
        return self.draw_card()

    def take_damage(self, amount: int) -> None:
        self.health -= max(amount, 0)

    def heal(self, amount: int) -> None:
        self.health = min(20, self.health + max(amount, 0))

    def remove_dead_units(self) -> list[UnitCard]:
        dead_units = [unit for unit in self.board if unit.health <= 0]
        self.board = [unit for unit in self.board if unit.health > 0]
        self.discard_pile.extend(dead_units)
        return dead_units

    def has_board_space(self) -> bool:
        backline_count = sum(1 for unit in self.board if not unit.in_frontline)
        return backline_count < MAX_BACKLINE_UNITS
