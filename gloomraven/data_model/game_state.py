from typing import List, Dict
from pydantic import field_validator, ConfigDict
from pydantic.alias_generators import to_snake, to_camel

from gloomraven.data_model.base_schema import BaseSchema
from gloomraven.data_model.characters import Character
from gloomraven.data_model.decks import AbilityDeck, ModifierDeck, LootDeck
from gloomraven.data_model.element_state import Elements, ElementLevel


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
    scenario_special_rules: List[str]
    scenario_sections_added: List[str]
    current_campaign: str
    current_list: List[Character]
    current_ability_decks: List[AbilityDeck]
    modifier_deck: ModifierDeck
    modifier_deck_allies: ModifierDeck
    loot_deck: LootDeck
    unlocked_classes: List[str]
    show_ally_deck: bool
    element_state: Dict[Elements, ElementLevel]

    @field_validator("element_state", mode="before")
    @classmethod
    def convert_dict_keys_and_values(cls, value: Dict[str, int]) -> Dict[Elements, ElementLevel]:
        if not isinstance(value, dict):
            raise ValueError("element_state must be a dictionary")
        try:
            return {
                Elements(int(element)): ElementLevel(state)
                for element, state in value.items()
            }
        except KeyError as exc:
            raise ValueError(f"Invalid element name: {exc.args[0]}") from exc
        except ValueError as exc:
            raise ValueError(f"Invalid state value: {exc.args[0]}") from exc