# -*- coding: UTF-8 -*-
from enum import Enum


class EDirections(Enum):
    """
    Left is the oldest entry in the queue, Right the newest
    """
    LEFT = 0
    RIGHT = 1