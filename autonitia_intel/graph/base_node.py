"""
Minimal node abstraction. Each node has a single responsibility and transforms
a shared `state` dict. This intentionally mirrors LangGraph's node contract so
the engine can be swapped for LangGraph later without rewriting nodes.
"""


class BaseNode:
    def __init__(self, name: str | None = None):
        self.name = name or self.__class__.__name__

    def execute(self, state: dict) -> dict:  # pragma: no cover - interface
        raise NotImplementedError
