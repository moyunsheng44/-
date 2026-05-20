from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from data.cards import CARD_LIBRARY, build_default_deck
from engine.effects import resolve_spell
from models.card import SpellCard, UnitCard
from models.player import MAX_BACKLINE_UNITS, MAX_FRONTLINE_UNITS, Player
from utils.display import describe_card, format_status, target_label


@dataclass(slots=True)
class Game:
    players: list[Player]
    current_player_index: int = 0
    turn_number: int = 0
    game_over: bool = False
    winner: Player | None = None
    logs: list[str] = field(default_factory=list)
    started: bool = False
    last_action: dict[str, Any] = field(default_factory=dict)
    last_mana_change: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_default_game(cls) -> "Game":
        players = [
            Player(name="玩家1", deck=build_default_deck()),
            Player(name="玩家2", deck=build_default_deck()),
        ]
        for player in players:
            player.shuffle_deck()
            for _ in range(3):
                player.draw_card()
        return cls(players=players)

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    @property
    def opponent(self) -> Player:
        return self.players[1 - self.current_player_index]

    def start_game(self) -> dict[str, Any]:
        self.logs.clear()
        self.turn_number = 1
        self.started = True
        self.last_action = {"kind": "start_game"}
        self.last_mana_change = {"kind": "turn_refill", "amount": 0, "before": 0, "after": 0, "label": "开局"}
        self._start_turn()
        return self.get_state()

    def get_state(self) -> dict[str, Any]:
        return {
            "turn_number": self.turn_number,
            "current_player": self._player_snapshot(self.current_player),
            "opponent": self._player_snapshot(self.opponent),
            "status_text": format_status(self.current_player, self.opponent),
            "logs": list(self.logs),
            "game_over": self.game_over,
            "winner": self.winner.name if self.winner else None,
            "help_text": self._help_text(),
            "max_backline_units": MAX_BACKLINE_UNITS,
            "max_frontline_units": MAX_FRONTLINE_UNITS,
            "last_action": dict(self.last_action),
            "last_mana_change": dict(self.last_mana_change),
            "card_library": self._card_library_snapshot(),
            "frontline_owner": self._frontline_owner_name(),
        }

    def play_card(self, hand_index: int, target: tuple[str, int | None] | None = None) -> str:
        self._require_active_game()
        player = self.current_player
        card = self._get_hand_card(hand_index)

        if card.cost > player.mana:
            raise ValueError("费用不足，无法打出这张牌。")

        before_mana = player.mana
        player.mana -= card.cost
        player.hand.pop(hand_index)
        self._record_mana_change("部署花费", card.cost, before_mana, player.mana)

        if isinstance(card, UnitCard):
            if not player.has_board_space():
                player.hand.insert(hand_index, card)
                player.mana += card.cost
                self._record_mana_change("部署返还", -card.cost, player.mana - card.cost, player.mana)
                raise ValueError("后方战场已满（总部+4单位=5卡），无法继续部署。")
            card.can_attack = False
            card.has_attacked_this_turn = True
            player.board.append(card)
            if any(e.trigger == "on_deploy" and e.effect_type == "blitz" for e in card.effects):
                card.has_moved_this_turn = False
                card.has_attacked_this_turn = False
                card.can_attack = True
            message = f"{player.name} 打出了单位【{card.name}】（{card.attack}/{card.health}）。"
            self.last_action = {"kind": "play_unit", "card_name": card.name}
            self._record(message)
            self._after_action()
            return message

        if isinstance(card, SpellCard):
            target_value = self._resolve_spell_target(card, target)
            message = resolve_spell(card, player, self.opponent, target_value)
            player.discard_pile.append(card)
            self.last_action = {"kind": "play_command", "card_name": card.name}
            self._record(message)
            self._after_action()
            return message

        raise ValueError("暂不支持这张牌的类型。")

    def move_to_frontline(self, unit_index: int) -> str:
        self._require_active_game()
        unit = self._get_friendly_unit(unit_index)
        owner = self._frontline_owner()
        if owner is self.opponent:
            raise ValueError("敌方仍然占领前线，必须先消灭敌方所有前线单位。")
        if unit.in_frontline:
            raise ValueError("这个单位已经在前线。")
        if len([board_unit for board_unit in self.current_player.board if board_unit.in_frontline]) >= MAX_FRONTLINE_UNITS:
            raise ValueError("前线已满，最多只能有 5 个友方单位。")
        if unit.has_moved_this_turn:
            raise ValueError("这个单位本回合已经移动过了。")
        if unit.unit_class == "步兵" and unit.has_attacked_this_turn:
            raise ValueError("步兵一回合只能移动或攻击，不能两者都做。")
        if unit.action_cost > self.current_player.mana:
            raise ValueError("费用不足，无法将这个单位推进到前线。")

        before_mana = self.current_player.mana
        self.current_player.mana -= unit.action_cost
        self._record_mana_change("移动花费", unit.action_cost, before_mana, self.current_player.mana)

        unit.in_frontline = True
        unit.has_moved_this_turn = True
        if unit.unit_class == "步兵":
            unit.can_attack = False
        else:
            unit.can_attack = not unit.has_attacked_this_turn
        message = f"{unit.name} 已推进到前线。"
        self.last_action = {"kind": "move_frontline", "unit_name": unit.name}
        self._record(message)
        return message

    def attack(self, attacker_index: int, target_kind: str, target_index: int | None = None) -> str:
        self._require_active_game()
        attacker = self._get_friendly_unit(attacker_index)

        if not attacker.can_attack:
            raise ValueError("这个单位本回合不能攻击。")
        if attacker.has_attacked_this_turn:
            raise ValueError("这个单位本回合已经攻击过了。")
        if attacker.action_cost > self.current_player.mana:
            raise ValueError("费用不足，无法发动这次攻击。")
        is_ground = attacker.unit_class in ("步兵", "坦克")
        if is_ground and not attacker.in_frontline:
            if target_kind == "enemy_player":
                raise ValueError("地面单位必须推进到前线才能攻击敌方总部。")
            if target_kind == "enemy_unit":
                defender = self._get_enemy_unit(target_index)
                if not defender.in_frontline:
                    raise ValueError("后方地面单位只能攻击敌方前线单位，不能攻击敌方后方单位。")

        before_mana = self.current_player.mana
        self.current_player.mana -= attacker.action_cost
        self._record_mana_change("攻击花费", attacker.action_cost, before_mana, self.current_player.mana)

        if target_kind == "enemy_player":
            self.opponent.take_damage(attacker.attack)
            attacker.has_attacked_this_turn = True
            attacker.can_attack = False
            if attacker.unit_class == "步兵":
                attacker.has_moved_this_turn = True
            message = (
                f"{attacker.name} 攻击了 {self.opponent.name} 总部，"
                f"造成了 {attacker.attack} 点伤害。"
            )
            self.last_action = {"kind": "attack_hq", "unit_name": attacker.name}
            self._record(message)
            self._after_action()
            return message

        if target_kind != "enemy_unit":
            raise ValueError("攻击目标类型无效。")
        if target_index is None:
            raise ValueError("请选择一个敌方单位作为攻击目标。")

        defender = self._get_enemy_unit(target_index)
        attacker.health -= defender.attack
        defender.health -= attacker.attack
        attacker.has_attacked_this_turn = True
        attacker.can_attack = False
        if attacker.unit_class == "步兵":
            attacker.has_moved_this_turn = True
        message = (
            f"{attacker.name} 攻击了 {defender.name}。"
            f"{attacker.name} 剩余 {attacker.health} 点生命，"
            f"{defender.name} 剩余 {defender.health} 点生命。"
        )
        self.last_action = {"kind": "attack_unit", "unit_name": attacker.name, "target_name": defender.name}
        self._record(message)
        self._after_action()
        return message

    def end_turn(self) -> str:
        self._require_active_game()
        message = f"{self.current_player.name} 结束了回合。"
        self._record(message)
        self.last_action = {"kind": "end_turn"}
        if self.game_over:
            return message
        self.current_player_index = 1 - self.current_player_index
        self.turn_number += 1
        self._start_turn()
        return message

    def _start_turn(self) -> None:
        current = self.current_player
        before_mana = current.mana
        drawn_card = current.start_turn()
        for unit in current.board:
            unit.reset_turn_state()
        self._record_mana_change("回合补充", current.mana - before_mana, before_mana, current.mana)
        self._record(f"========== 第 {self.turn_number} 回合 ==========")
        self._record(f"当前行动玩家：{current.name}")
        if drawn_card == "overdraw":
            self._record(f"{current.name} 手牌已满（10张），抽到的牌被弃置！（爆牌）")
        elif drawn_card is None:
            self._record(f"{current.name} 想抽牌，但牌库已经空了。")
        else:
            self._record(f"{current.name} 抽到了【{drawn_card.name}】。")
        self._record(f"{current.name} 当前费用：{current.mana}/{current.max_mana}。")
        self._record(f"{current.name} 当前战场容量：{len(current.board) + 1}/5（含总部）。")
        self.last_action = {"kind": "turn_start", "player": current.name, "turn": self.turn_number}

    def _after_action(self) -> None:
        self.cleanup_dead_units()
        self.check_winner()
        if self.game_over:
            if self.winner is None:
                self._record("游戏结束，双方同时倒下。")
            else:
                self._record(f"游戏结束，胜利者是 {self.winner.name}。")

    def cleanup_dead_units(self) -> None:
        for player in self.players:
            dead_units = player.remove_dead_units()
            for unit in dead_units:
                self._record(f"【{unit.name}】被摧毁并进入弃牌堆。")

    def check_winner(self) -> None:
        alive_players = [player for player in self.players if player.health > 0]
        if len(alive_players) == 1:
            self.game_over = True
            self.winner = alive_players[0]
        elif len(alive_players) == 0:
            self.game_over = True
            self.winner = None

    def reset_game(self) -> dict[str, Any]:
        fresh = self.create_default_game()
        self.players = fresh.players
        self.current_player_index = fresh.current_player_index
        self.turn_number = fresh.turn_number
        self.game_over = fresh.game_over
        self.winner = fresh.winner
        self.logs = []
        self.started = False
        self.last_action = {}
        self.last_mana_change = {}
        return self.start_game()

    def _player_snapshot(self, player: Player) -> dict[str, Any]:
        frontline = [(i, unit) for i, unit in enumerate(player.board) if unit.in_frontline]
        backline = [(i, unit) for i, unit in enumerate(player.board) if not unit.in_frontline]
        return {
            "name": player.name,
            "health": player.health,
            "mana": player.mana,
            "max_mana": player.max_mana,
            "deck_count": len(player.deck),
            "hand_count": len(player.hand),
            "hand": [
                {
                    "index": index,
                    "text": describe_card(card),
                    "card_type": card.card_type,
                    "name": card.name,
                    "cost": card.cost,
                    "target_type": card.target_type if isinstance(card, SpellCard) else None,
                    "effect_type": card.effect_type if isinstance(card, SpellCard) else None,
                    "effect_value": card.effect_value if isinstance(card, SpellCard) else None,
                    "attack": card.attack if isinstance(card, UnitCard) else None,
                    "health": card.health if isinstance(card, UnitCard) else None,
                    "unit_class": card.unit_class if isinstance(card, UnitCard) else None,
                    "action_cost": card.action_cost if isinstance(card, UnitCard) else None,
                    "description": card.description,
                    "emblem": card.emblem,
                    "effects": [
                        {"trigger": e.trigger, "effect_type": e.effect_type,
                         "value": e.value, "target": e.target,
                         "description": e.description}
                        for e in card.effects
                    ] if isinstance(card, UnitCard) else [],
                }
                for index, card in enumerate(player.hand)
            ],
            "board": [self._unit_snapshot(index, unit) for index, unit in enumerate(player.board)],
            "frontline": [self._unit_snapshot(i, unit) for i, unit in frontline],
            "backline": [self._unit_snapshot(i, unit) for i, unit in backline],
        }

    def _unit_snapshot(self, index: int, unit: UnitCard) -> dict[str, Any]:
        return {
            "index": index,
            "name": unit.name,
            "cost": unit.cost,
            "attack": unit.attack,
            "health": unit.health,
            "can_attack": unit.can_attack,
            "text": unit.describe(),
            "unit_class": unit.unit_class,
            "action_cost": unit.action_cost,
            "description": unit.description,
            "emblem": unit.emblem,
            "in_frontline": unit.in_frontline,
            "has_moved_this_turn": unit.has_moved_this_turn,
            "has_attacked_this_turn": unit.has_attacked_this_turn,
            "effects": [
                {"trigger": e.trigger, "effect_type": e.effect_type,
                 "value": e.value, "target": e.target,
                 "description": e.description}
                for e in unit.effects
            ],
        }

    def _help_text(self) -> str:
        return (
            "操作说明：\n"
            "1. 前线同一时间只能由一方占领。若敌方已占领前线，必须先消灭其所有前线单位。\n"
            "2. 指令牌如果需要目标，请先选牌，再选单位或总部按钮。\n"
            "3. 后方地面单位可攻击敌方前线单位；须推进到前线才能攻击敌方后方或总部。\n"
            "4. 步兵一回合只能移动或攻击；坦克一回合可以移动并攻击。\n"
            "5. 每位玩家后方战场最多容纳 5 张卡牌（总部占据 1 张，因此最多部署 4 个单位）。"
            "\n6. 前线战场最多容纳 5 个友方单位。每个战场独立计数。"
        "\n7. 每人最多持有 10 张手牌，超出部分将被弃置（爆牌）。"
        )

    def _card_library_snapshot(self) -> list[dict[str, Any]]:
        return [dict(card) for card in CARD_LIBRARY]

    def _record(self, message: str) -> None:
        self.logs.append(message)

    def _record_mana_change(self, label: str, amount: int, before: int, after: int) -> None:
        self.last_mana_change = {
            "label": label,
            "amount": amount,
            "before": before,
            "after": after,
        }

    def _frontline_owner(self) -> Player | None:
        if any(unit.in_frontline for unit in self.current_player.board):
            return self.current_player
        if any(unit.in_frontline for unit in self.opponent.board):
            return self.opponent
        return None

    def _frontline_owner_name(self) -> str | None:
        owner = self._frontline_owner()
        return owner.name if owner else None

    def _get_hand_card(self, hand_index: int) -> UnitCard | SpellCard:
        try:
            return self.current_player.hand[hand_index]
        except IndexError as error:
            raise ValueError("手牌编号超出范围。") from error

    def _get_friendly_unit(self, unit_index: int) -> UnitCard:
        try:
            return self.current_player.board[unit_index]
        except IndexError as error:
            raise ValueError("我方单位编号超出范围。") from error

    def _get_enemy_unit(self, unit_index: int) -> UnitCard:
        try:
            return self.opponent.board[unit_index]
        except IndexError as error:
            raise ValueError("敌方单位编号超出范围。") from error

    def _resolve_spell_target(
        self,
        card: SpellCard,
        target: tuple[str, int | None] | None,
    ) -> str | None:
        if card.target_type is None:
            return None
        if target is None:
            raise ValueError(f"这张牌需要指定目标：{target_label(card.target_type)}。")
        target_kind, target_index = target
        if card.target_type == "enemy_player":
            if target_kind != "enemy_player":
                raise ValueError("这张牌只能选择敌方总部作为目标。")
            return "0"
        if card.target_type == "enemy_unit":
            if target_kind != "enemy_unit" or target_index is None:
                raise ValueError("这张牌需要选择一个敌方单位作为目标。")
            return str(target_index)
        if card.target_type == "ally_player":
            if target_kind != "ally_player":
                raise ValueError("这张牌只能选择我方总部作为目标。")
            return "0"
        if card.target_type == "ally_unit":
            if target_kind != "ally_unit" or target_index is None:
                raise ValueError("这张牌需要选择一个我方单位作为目标。")
            return str(target_index)
        raise ValueError("这张牌的目标类型暂不支持。")

    def _require_active_game(self) -> None:
        if not self.started:
            raise ValueError("游戏尚未开始。")
        if self.game_over:
            raise ValueError("游戏已经结束。")
