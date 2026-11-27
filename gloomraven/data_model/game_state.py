from typing import Any

from pydantic import Field, field_validator

from gloomraven.data_model.base_schema import BaseSchema
from gloomraven.data_model.characters import MonsterCharacter, PlayerCharacter
from gloomraven.data_model.decks import AbilityDeck, LootDeck, ModifierDeck
from gloomraven.data_model.element_state import Element, ElementLevel


class SpecialRule(BaseSchema):
    # Mirrors X-Haven's SpecialRule, with the same defaults for fields it leaves out
    type: str
    name: str = ""
    note: str = ""
    health: str = ""  # X-Haven sends this as a string, also when it is a number or formula
    condition: str = ""
    init: int = 99
    level: int = 0
    start_of_round: bool = True
    entries: list[Any] = Field(default_factory=list, alias="list")


class GameState(BaseSchema):
    level: int
    solo: bool
    auto_scenario_level: bool
    difficulty: int
    round_state: int
    round: int
    total_rounds: int
    scenario: str
    toast_message: str
    scenario_special_rules: list[SpecialRule]
    scenario_sections_added: list[str]
    current_campaign: str
    current_list: list[PlayerCharacter | MonsterCharacter]
    current_ability_decks: list[AbilityDeck]
    modifier_deck: ModifierDeck
    modifier_deck_allies: ModifierDeck
    loot_deck: LootDeck
    unlocked_classes: list[str]
    show_ally_deck: bool
    element_state: dict[Element, ElementLevel]

    @field_validator("element_state", mode="before")
    @classmethod
    def convert_dict_keys_and_values(cls, value: dict[str, int]) -> dict[Element, ElementLevel]:
        if not isinstance(value, dict):
            raise ValueError("element_state must be a dictionary")
        try:
            return {Element(int(element)): ElementLevel(state) for element, state in value.items()}
        except KeyError as exc:
            raise ValueError(f"Invalid element name: {exc.args[0]}") from exc
        except ValueError as exc:
            raise ValueError(f"Invalid state value: {exc.args[0]}") from exc
