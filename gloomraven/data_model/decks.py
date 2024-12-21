from typing import Any, Dict, List

from gloomraven.data_model.base_schema import BaseSchema


class DrawPileCard(BaseSchema):
    nr: int
    deck: str


class AbilityDeck(BaseSchema):
    name: str
    draw_pile: List[DrawPileCard]
    discard_pile: List[DrawPileCard]
    last_round_drawn: int


class ModifierDeck(BaseSchema):
    blesses: int
    curses: int
    enfeebles: int
    added_minus_ones: int
    bad_omen: int
    draw_pile: List[Dict[str, str]]
    discard_pile: List[Any]


class LootDeck(BaseSchema):
    draw_pile: List[Any]
    discard_pile: List[Any]
    added_cards: List[int]
    enhancements: Dict[str, Any]
