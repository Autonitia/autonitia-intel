"""
Graph executor with conditional edges.

A graph is: nodes (keyed by name) + an `edges` map + an `entry` node. Each edge
value is one of:
  - a node name (str)        → always go there next
  - None (END)               → stop
  - a callable(state) -> str|None → CONDITIONAL: decide the next node at runtime

This makes the pipeline a real graph: branches (repair vs continue), short-circuits
(skip the LLM when there's nothing to do), and bounded loops. Still mirrors
LangGraph's contract so it can be swapped later. `max_steps` guards against loops.
"""

import time

from .base_node import BaseNode

END = None


class BaseGraph:
    def __init__(self, nodes: list[BaseNode], edges: dict, entry: str,
                 verbose: bool = True, max_steps: int = 25):
        self.nodes = {n.name: n for n in nodes}
        self.edges = edges
        self.entry = entry
        self.verbose = verbose
        self.max_steps = max_steps

    def execute(self, state: dict) -> dict:
        trace = []
        current = self.entry
        steps = 0

        while current is not None:
            if steps >= self.max_steps:
                raise RuntimeError(f"Graph exceeded max_steps={self.max_steps} (possible loop)")
            if current not in self.nodes:
                raise KeyError(f"Edge points to unknown node '{current}'")

            node = self.nodes[current]
            start = time.time()
            try:
                state = node.execute(state)
            except Exception as e:
                elapsed = int((time.time() - start) * 1000)
                trace.append({"node": current, "status": "error", "ms": elapsed, "error": str(e)})
                if self.verbose:
                    print(f"   ✗ {current} failed: {e}")
                state["_trace"] = trace
                state["_error"] = {"node": current, "error": str(e)}
                raise
            elapsed = int((time.time() - start) * 1000)
            trace.append({"node": current, "status": "success", "ms": elapsed})
            if self.verbose:
                print(f"   ✓ {current} ({elapsed} ms)")

            nxt = self.edges.get(current, END)
            current = nxt(state) if callable(nxt) else nxt
            steps += 1

        state["_trace"] = trace
        return state
