from data.cards import build_default_deck
from engine.effects import resolve_spell
from models.card import SpellCard, UnitCard
from models.player import Player


def test_draw_spell_adds_cards_to_hand() -> None:
    caster = Player(name="玩家A", deck=build_default_deck())
    opponent = Player(name="玩家B", deck=[])
    spell = SpellCard(
        id="draw_1",
        name="Supply Test",
        cost=1,
        card_type="spell",
        effect_type="draw",
        effect_value=2,
        target_type=None,
    )

    message = resolve_spell(spell, caster, opponent, None)

    assert len(caster.hand) == 2
    assert "抽到了" in message


def test_damage_spell_hits_enemy_unit() -> None:
    caster = Player(name="玩家A", deck=[])
    opponent = Player(name="玩家B", deck=[])
    opponent.board.append(
        UnitCard(
            id="unit_1",
            name="木桩单位",
            cost=1,
            card_type="unit",
            attack=1,
            health=4,
        )
    )
    spell = SpellCard(
        id="spell_1",
            name="测试轰炸",
        cost=1,
        card_type="spell",
        effect_type="damage",
        effect_value=2,
        target_type="enemy_unit",
    )

    resolve_spell(spell, caster, opponent, "0")

    assert opponent.board[0].health == 2
