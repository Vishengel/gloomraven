from typing import List, Any, Optional

from pydantic import BaseModel

from gloomraven.data_model.base_schema import BaseSchema


class CharacterState(BaseSchema):
    initiative: int
    health: int
    maxHealth: int
    level: int
    xp: int
    chill: int
    display: str
    summon_list: List[Any]
    conditions: List[int]
    conditions_added_this_turn: List[Any]
    conditions_added_previous_turn: List[Any]


class Character(BaseSchema):
    id: str
    turn_state: int


class PlayerCharacter(Character):
    character_state: Optional[CharacterState]
    character_class: Optional[str]


class MonsterCharacter(Character):
    is_active: Optional[bool]
    is_ally: Optional[bool]
    level: Optional[int]
    monster_instances: Optional[List[Any]]
    type: Optional[str]
