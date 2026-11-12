"""Persistence boundary for problem-resolution records.

The in-memory adapter is intentionally a test/vertical-slice implementation.
A durable adapter can implement the same protocol without changing domain rules.
"""
from __future__ import annotations

from copy import deepcopy
from threading import RLock
from typing import Protocol

from .resolution import ActionProposal, Commitment, Outcome, Responsibility


class ResolutionRepository(Protocol):
    def save_responsibility(self, item: Responsibility) -> None: ...
    def get_responsibility(self, item_id: str) -> Responsibility | None: ...
    def save_proposal(self, item: ActionProposal) -> None: ...
    def get_proposal(self, item_id: str) -> ActionProposal | None: ...
    def save_commitment(self, item: Commitment) -> None: ...
    def get_commitment(self, item_id: str) -> Commitment | None: ...
    def save_outcome(self, item: Outcome) -> None: ...
    def get_outcome(self, item_id: str) -> Outcome | None: ...


class InMemoryResolutionRepository:
    """Process-local adapter; never represent this as production durable storage."""

    def __init__(self) -> None:
        self._responsibilities: dict[str, Responsibility] = {}
        self._proposals: dict[str, ActionProposal] = {}
        self._commitments: dict[str, Commitment] = {}
        self._outcomes: dict[str, Outcome] = {}
        self._lock = RLock()

    def save_responsibility(self, item: Responsibility) -> None:
        with self._lock:
            self._responsibilities[item.id] = deepcopy(item)

    def get_responsibility(self, item_id: str) -> Responsibility | None:
        with self._lock:
            item = self._responsibilities.get(item_id)
            return deepcopy(item) if item else None

    def save_proposal(self, item: ActionProposal) -> None:
        with self._lock:
            self._proposals[item.id] = deepcopy(item)

    def get_proposal(self, item_id: str) -> ActionProposal | None:
        with self._lock:
            item = self._proposals.get(item_id)
            return deepcopy(item) if item else None

    def save_commitment(self, item: Commitment) -> None:
        with self._lock:
            self._commitments[item.id] = deepcopy(item)

    def get_commitment(self, item_id: str) -> Commitment | None:
        with self._lock:
            item = self._commitments.get(item_id)
            return deepcopy(item) if item else None

    def save_outcome(self, item: Outcome) -> None:
        with self._lock:
            self._outcomes[item.id] = deepcopy(item)

    def get_outcome(self, item_id: str) -> Outcome | None:
        with self._lock:
            item = self._outcomes.get(item_id)
            return deepcopy(item) if item else None
