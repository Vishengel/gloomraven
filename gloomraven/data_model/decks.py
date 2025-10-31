from typing import Any

from gloomraven.data_model.base_schema import BaseSchema


class DrawPileCard(BaseSchema):
    nr: int
    deck: str


class AbilityDeck(BaseSchema):
    name: str
    draw_pile: list[DrawPileCard]
    discard_pile: list[DrawPileCard]
    last_round_drawn: int


class ModifierDeck(BaseSchema):
    bad_omen: int
    corrosive_spew: bool
    added_minus_ones: int
    bad_omen: int
    draw_pile: list[dict[str, str]]
    discard_pile: list[Any]
    removed_pile: list[Any]


class LootDeck(BaseSchema):
    draw_pile: list[Any]
    discard_pile: list[Any]
    added_cards: list[int]
    enhancements: dict[str, Any]
