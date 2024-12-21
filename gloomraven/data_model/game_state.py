from typing import Dict, List, Union

from pydantic import field_validator

from gloomraven.data_model.base_schema import BaseSchema
from gloomraven.data_model.characters import MonsterCharacter, PlayerCharacter
from gloomraven.data_model.decks import AbilityDeck, LootDeck, ModifierDeck
from gloomraven.data_model.element_state import Element, ElementLevel


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
    current_list: List[Union[PlayerCharacter, MonsterCharacter]]
    current_ability_decks: List[AbilityDeck]
    modifier_deck: ModifierDeck
    modifier_deck_allies: ModifierDeck
    loot_deck: LootDeck
    unlocked_classes: List[str]
    show_ally_deck: bool
    element_state: Dict[Element, ElementLevel]

    @field_validator("element_state", mode="before")
    @classmethod
    def convert_dict_keys_and_values(
        cls, value: Dict[str, int]
    ) -> Dict[Element, ElementLevel]:
        if not isinstance(value, dict):
            raise ValueError("element_state must be a dictionary")
        try:
            return {
                Element(int(element)): ElementLevel(state)
                for element, state in value.items()
            }
        except KeyError as exc:
            raise ValueError(f"Invalid element name: {exc.args[0]}") from exc
        except ValueError as exc:
            raise ValueError(f"Invalid state value: {exc.args[0]}") from exc
