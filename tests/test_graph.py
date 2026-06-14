"""Unit tests for the conditional graph engine and the profile-pipeline router."""

import pytest

from autonitia_intel.graph import END, BaseGraph
from autonitia_intel.graph.base_node import BaseNode
from autonitia_intel.graph.profile_graph import _after_extraction
from autonitia_intel.models import FactExtraction


# ── Tiny nodes for engine tests ────────────────────────────────

class _Append(BaseNode):
    def __init__(self, name, tag):
        super().__init__(name)
        self.tag = tag

    def execute(self, state):
        state.setdefault("log", []).append(self.tag)
        return state


def test_linear_flow():
    g = BaseGraph(
        nodes=[_Append("A", "a"), _Append("B", "b"), _Append("C", "c")],
        edges={"A": "B", "B": "C", "C": END},
        entry="A", verbose=False,
    )
    out = g.execute({})
    assert out["log"] == ["a", "b", "c"]
    assert [t["node"] for t in out["_trace"]] == ["A", "B", "C"]


def test_conditional_branch_taken():
    def route(state):
        return "B" if state.get("go_b") else "C"

    g = BaseGraph(
        nodes=[_Append("A", "a"), _Append("B", "b"), _Append("C", "c")],
        edges={"A": route, "B": END, "C": END},
        entry="A", verbose=False,
    )
    assert g.execute({"go_b": True})["log"] == ["a", "b"]
    assert g.execute({"go_b": False})["log"] == ["a", "c"]


def test_loop_guard_raises():
    g = BaseGraph(
        nodes=[_Append("A", "a")],
        edges={"A": "A"},   # infinite self-loop
        entry="A", verbose=False, max_steps=5,
    )
    with pytest.raises(RuntimeError, match="max_steps"):
        g.execute({})


def test_unknown_edge_raises():
    g = BaseGraph(nodes=[_Append("A", "a")], edges={"A": "Nope"}, entry="A", verbose=False)
    with pytest.raises(KeyError):
        g.execute({})


# ── Profile-pipeline repair router ─────────────────────────────

def test_repair_branch_when_no_company():
    state = {"facts": FactExtraction(company_name=""), "repaired": False}
    assert _after_extraction(state) == "RepairExtractionNode"


def test_no_repair_when_company_found():
    state = {"facts": FactExtraction(company_name="Acme"), "repaired": False}
    assert _after_extraction(state) == "PositiveDetectionNode"


def test_no_infinite_repair():
    state = {"facts": FactExtraction(company_name=""), "repaired": True}
    assert _after_extraction(state) == "PositiveDetectionNode"  # already repaired → move on
