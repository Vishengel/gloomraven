from enum import Enum


class Element(Enum):
    FIRE = 0
    ICE = 1
    AIR = 2
    EARTH = 3
    LIGHT = 4
    DARK = 5

    def __repr__(self):
        return self.name


class ElementLevel(Enum):
    FULL = 0
    HALF = 1
    INERT = 2

    def __repr__(self):
        return self.name
