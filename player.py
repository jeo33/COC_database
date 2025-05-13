# Install pydantic if you haven’t already:
#    pip install pydantic

from pydantic import BaseModel
from typing import List, Optional
import json

# 1) Define your models

class BadgeUrls(BaseModel):
    small: str
    medium: str
    large: str

class Clan(BaseModel):
    tag: str
    name: str
    clanLevel: int
    badgeUrls: BadgeUrls

class IconUrls(BaseModel):
    small: str
    tiny: str
    medium: str

class League(BaseModel):
    id: int
    name: str
    iconUrls: IconUrls

class Achievement(BaseModel):
    name: str
    stars: int
    value: int
    target: int
    info: str
    completionInfo: Optional[str]
    village: str

class Troop(BaseModel):
    name: str
    level: int
    maxLevel: int
    village: str
    superTroopIsActive: Optional[bool] = False

class Player(BaseModel):
    tag: str
    name: str
    townHallLevel: int
    trophies: int
    bestTrophies: int
    clan: Optional[Clan]
    league: League
    achievements: List[Achievement]
    troops: List[Troop]