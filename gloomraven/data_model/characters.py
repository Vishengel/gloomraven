from typing import Any

from gloomraven.data_model.base_schema import BaseSchema


class CharacterState(BaseSchema):
    initiative: int
    health: int
    maxHealth: int
    level: int
    xp: int
    chill: int
    display: str
    summon_list: list[Any]
    conditions: list[int]
    conditions_added_this_turn: list[Any]
    conditions_added_previous_turn: list[Any]


class Character(BaseSchema):
    id: str
    turn_state: int


class PlayerCharacter(Character):
    character_state: CharacterState | None
    character_class: str | None


class MonsterCharacter(Character):
    is_active: bool | None
    is_ally: bool | None
    level: int | None
    monster_instances: list[Any] | None
    type: str | None
