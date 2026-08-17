"""Task Graph (DAG) for JARVIS Phase 23.

Provides a directed acyclic graph for goal tasks with topological
sorting, parallel group detection, and cycle detection.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("jarvis.agent.task_graph")


@dataclass
class GraphNode:
    task_id: str
    data: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.task_id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, GraphNode) and self.task_id == other.task_id


@dataclass
class TaskGraph:
    """DAG-based task graph for goal execution."""
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: dict[str, set[str]] = field(default_factory=dict)
    reverse_edges: dict[str, set[str]] = field(default_factory=dict)

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.task_id] = node
        self.edges.setdefault(node.task_id, set())
        self.reverse_edges.setdefault(node.task_id, set())

    def add_edge(self, from_id: str, to_id: str) -> None:
        if from_id not in self.nodes or to_id not in self.nodes:
            raise ValueError(f"Cannot add edge: node not found ({from_id} -> {to_id})")
        self.edges[from_id].add(to_id)
        self.reverse_edges[to_id].add(from_id)

    def get_dependencies(self, task_id: str) -> set[str]:
        return self.reverse_edges.get(task_id, set())

    def get_dependents(self, task_id: str) -> set[str]:
        return self.edges.get(task_id, set())

    def topological_sort(self) -> list[str]:
        in_degree = {tid: len(self.reverse_edges.get(tid, set())) for tid in self.nodes}
        queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        order: list[str] = []

        while queue:
            node_id = queue.popleft()
            order.append(node_id)
            for dependent in self.edges.get(node_id, set()):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(order) != len(self.nodes):
            raise ValueError("Task graph contains a cycle")
        return order

    def get_parallel_groups(self) -> list[list[str]]:
        """Return groups of tasks that can run in parallel."""
        order = self.topological_sort()
        groups: list[list[str]] = []
        completed: set[str] = set()
        remaining = list(order)

        while remaining:
            ready = [tid for tid in remaining if all(d in completed for d in self.reverse_edges.get(tid, set()))]
            if not ready:
                ready = remaining
            groups.append(ready)
            for tid in ready:
                completed.add(tid)
                remaining.remove(tid)

        return groups

    def get_critical_path(self) -> list[str]:
        order = self.topological_sort()
        earliest_start: dict[str, int] = {}
        for tid in order:
            deps = self.reverse_edges.get(tid, set())
            if not deps:
                earliest_start[tid] = 0
            else:
                earliest_start[tid] = max(earliest_start[d] + 1 for d in deps)

        max_time = max(earliest_start.values()) if earliest_start else 0
        critical: list[str] = []
        current_time = max_time
        for tid in reversed(order):
            if earliest_start.get(tid, 0) == current_time:
                critical.append(tid)
                current_time -= 1
        critical.reverse()
        return critical

    def validate(self) -> bool:
        try:
            self.topological_sort()
            return True
        except ValueError:
            return False

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": {tid: n.data for tid, n in self.nodes.items()},
            "edges": {k: list(v) for k, v in self.edges.items()},
            "parallel_groups": self.get_parallel_groups(),
            "critical_path": self.get_critical_path(),
        }
