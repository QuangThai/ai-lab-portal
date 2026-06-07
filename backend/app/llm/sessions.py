"""Agent session store for preserving run state across approval gates (US-094).

Stores serialized ``RunState`` from Agent SDK runs so that when a human
approves a stage, the agent can resume from where it paused rather than
starting fresh. This enables the pipeline continuity needed for human-in-
the-loop workflows.

Storage is in-memory by default; Redis-backed storage can be added when
the session store moves to production.
"""

from __future__ import annotations

from typing import Any

from agents.run import RunState


class AgentSessionStore:
    """Stores serialized agent run state keyed by entity (idea) ID.

    Each entry stores the ``RunState.to_json()`` output so the session
    can be serialized to disk or a database later.

    Attributes:
        _sessions: Mapping of ``entity_id`` to serialized state dicts.
    """

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def save(
        self,
        entity_id: str,
        state: RunState,
        *,
        agent_name: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Persist an agent run state for later resumption.

        Args:
            entity_id: The entity ID (e.g. blog idea ID) to key on.
            state: The ``RunState`` to save (serialized via ``to_json()``).
            agent_name: Optional name of the last agent (for debugging).
            metadata: Optional metadata dict.

        Returns:
            The session ID (same as ``entity_id`` for now).
        """
        raw = RunState.to_json(state)
        self._sessions[entity_id] = {
            "state_raw": raw,
            "agent_name": agent_name,
            "metadata": metadata or {},
        }
        return entity_id

    def load(self, entity_id: str, initial_agent: Any) -> RunState | None:
        """Load a previously saved run state for resumption.

        Args:
            entity_id: The entity ID to look up.
            initial_agent: The agent instance to deserialize against
                (required by ``RunState.from_json()``).

        Returns:
            The deserialized ``RunState``, or ``None`` if no session exists.
        """
        entry = self._sessions.get(entity_id)
        if entry is None:
            return None
        return RunState.from_json(initial_agent, entry["state_raw"])

    def drop(self, entity_id: str) -> None:
        """Remove a stored session (e.g. after pipeline completes)."""
        self._sessions.pop(entity_id, None)

    def has_session(self, entity_id: str) -> bool:
        """Check whether a session exists for the given entity."""
        return entity_id in self._sessions

    def clear(self) -> None:
        """Remove all sessions (for tests)."""
        self._sessions.clear()


# Module-level singleton for app-wide access.
_global_store: AgentSessionStore | None = None


def get_session_store() -> AgentSessionStore:
    """Get or create the global agent session store."""
    global _global_store
    if _global_store is None:
        _global_store = AgentSessionStore()
    return _global_store
