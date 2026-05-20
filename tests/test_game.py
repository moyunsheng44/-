from engine.game import Game
from models.card import SpellCard, UnitCard
from models.player import Player


def test_start_game_draws_card_and_sets_turn_state() -> None:
    game = Game.create_default_game()

    state = game.start_game()

    assert state["turn_number"] == 1
    assert state["current_player"]["name"] == "玩家1"
    assert any("当前行动玩家" in log for log in state["logs"])


def test_playing_unit_spends_mana_and_adds_to_board() -> None:
    unit = UnitCard(
        id="u1",
        name="步兵",
        cost=1,
        card_type="unit",
        attack=2,
        health=2,
    )
    player = Player(name="玩家1", deck=[], mana=2, max_mana=2, hand=[unit])
    opponent = Player(name="玩家2", deck=[])
    game = Game(players=[player, opponent], started=True, turn_number=1)

    message = game.play_card(0, None)

    assert "打出了单位" in message
    assert player.mana == 1
    assert len(player.board) == 1
    assert len(player.hand) == 0


def test_unit_can_attack_player_only_once_per_turn() -> None:
    attacker = UnitCard(
        id="u1",
        name="突击兵",
        cost=1,
        card_type="unit",
        attack=3,
        health=2,
        unit_class="坦克",
    )
    attacker.can_attack = True
    attacker.in_frontline = True
    player = Player(name="玩家1", deck=[], board=[attacker])
    opponent = Player(name="玩家2", deck=[])
    game = Game(players=[player, opponent], started=True, turn_number=1)

    message = game.attack(0, "enemy_player")

    assert "攻击了 玩家2 总部" in message
    assert opponent.health == 17
    assert attacker.can_attack is False


def test_playing_spell_moves_it_to_discard() -> None:
    spell = SpellCard(
        id="s1",
        name="打击",
        cost=2,
        card_type="spell",
        effect_type="damage",
        effect_value=3,
        target_type="enemy_player",
    )
    player = Player(name="玩家1", deck=[], mana=2, max_mana=2, hand=[spell])
    opponent = Player(name="玩家2", deck=[])
    game = Game(players=[player, opponent], started=True, turn_number=1)

    message = game.play_card(0, ("enemy_player", None))

    assert "造成了 3 点伤害" in message
    assert len(player.discard_pile) == 1
    assert opponent.health == 17


def test_end_turn_switches_player_and_starts_new_turn() -> None:
    game = Game.create_default_game()
    game.start_game()

    game.end_turn()
    state = game.get_state()

    assert state["turn_number"] == 2
    assert state["current_player"]["name"] == "玩家2"
