from enum import Enum


class Elements(Enum):
    Fire = 0
    Ice = 1
    Air = 2
    Earth = 3
    Light = 4
    Dark = 5

    def __repr__(self):
        return self.name


class ElementLevel(Enum):
    Full = 0
    Half = 1
    Inert = 2

    def __repr__(self):
        return self.name
