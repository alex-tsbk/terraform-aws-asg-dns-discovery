import json
from typing import Any


def to_json(o: Any):
    """Returns JSON representation of a given object"""
    return json.dumps(o, default=str)
