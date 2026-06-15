"""
Multi-agent architecture profiles for Rogue Resilience experiments.

Each profile defines agent topology, routing rules, injection targets, and
expected detection points for chaos experiments.
"""

from dataclasses import dataclass, field
from typing import Dict, List

from rogue.resilience.models import ArchitectureId


@dataclass(frozen=True)
class AgentRole:
    """
    Role definition for an agent in a multi-agent system.

    Attributes:
        agent_id: Stable identifier used in traces and entrypoint routing.
        role: Logical role name (supervisor, worker, peer, etc.).
        description: Human-readable description of the agent's responsibility.
    """

    agent_id: str
    role: str
    description: str = ""


@dataclass(frozen=True)
class ArchitectureProfile:
    """
    Complete architecture profile for a multi-agent resilience experiment.

    Attributes:
        id: Architecture identifier matching ``ArchitectureId``.
        name: Display name for reports and UI.
        description: Summary of the topology and what it tests.
        agents: All agents participating in the system.
        entry_agent_id: Agent that receives baseline and recovery tasks.
        default_injection_target: Default agent to fault if none specified.
        detection_agents: Agents expected to flag rogue behavior.
        notify_on_fault: Map of injection target -> peers notified after fault.
    """

    id: ArchitectureId
    name: str
    description: str
    agents: List[AgentRole]
    entry_agent_id: str
    default_injection_target: str
    detection_agents: List[str] = field(default_factory=list)
    notify_on_fault: Dict[str, List[str]] = field(default_factory=dict)

    @property
    def agent_ids(self) -> List[str]:
        """Return ordered list of agent IDs in this profile."""
        return [agent.agent_id for agent in self.agents]

    def is_multi_agent(self) -> bool:
        """Return True if this profile involves more than one agent."""
        return len(self.agents) > 1


ARCHITECTURE_CATALOG: Dict[ArchitectureId, ArchitectureProfile] = {
    ArchitectureId.SINGLE_AGENT: ArchitectureProfile(
        id=ArchitectureId.SINGLE_AGENT,
        name="Single Agent",
        description="One agent with no inter-agent routing (Phase 1 default).",
        agents=[AgentRole("default", "agent", "Standalone agent under test")],
        entry_agent_id="default",
        default_injection_target="default",
        detection_agents=["default"],
    ),
    ArchitectureId.HIERARCHICAL: ArchitectureProfile(
        id=ArchitectureId.HIERARCHICAL,
        name="Hierarchical Supervisor-Worker",
        description=(
            "Supervisor delegates to workers; tests detection and cascade "
            "when a worker goes rogue."
        ),
        agents=[
            AgentRole("supervisor", "supervisor", "Routes tasks and monitors workers"),
            AgentRole("worker-1", "worker", "Primary worker agent"),
            AgentRole("worker-2", "worker", "Secondary worker agent"),
        ],
        entry_agent_id="supervisor",
        default_injection_target="worker-1",
        detection_agents=["supervisor"],
        notify_on_fault={
            "worker-1": ["supervisor", "worker-2"],
            "worker-2": ["supervisor", "worker-1"],
        },
    ),
    ArchitectureId.PEER_TO_PEER: ArchitectureProfile(
        id=ArchitectureId.PEER_TO_PEER,
        name="Peer-to-Peer",
        description=(
            "Fully connected peers; tests cascading failure when one peer "
            "broadcasts rogue output."
        ),
        agents=[
            AgentRole("peer-a", "peer", "Collaborating peer A"),
            AgentRole("peer-b", "peer", "Collaborating peer B"),
            AgentRole("peer-c", "peer", "Collaborating peer C"),
        ],
        entry_agent_id="peer-a",
        default_injection_target="peer-b",
        detection_agents=["peer-a", "peer-c"],
        notify_on_fault={
            "peer-a": ["peer-b", "peer-c"],
            "peer-b": ["peer-a", "peer-c"],
            "peer-c": ["peer-a", "peer-b"],
        },
    ),
    ArchitectureId.SUPERVISOR_WORKER: ArchitectureProfile(
        id=ArchitectureId.SUPERVISOR_WORKER,
        name="Supervisor-Worker Pipeline",
        description="Sequential supervisor delegating to workers one at a time.",
        agents=[
            AgentRole("supervisor", "supervisor", "Pipeline coordinator"),
            AgentRole("worker-1", "worker", "First pipeline stage"),
            AgentRole("worker-2", "worker", "Second pipeline stage"),
        ],
        entry_agent_id="supervisor",
        default_injection_target="worker-1",
        detection_agents=["supervisor"],
        notify_on_fault={"worker-1": ["supervisor", "worker-2"]},
    ),
}


def get_architecture(architecture_id: ArchitectureId | str) -> ArchitectureProfile:
    """
    Look up an architecture profile by ID.

    Args:
        architecture_id: Architecture enum value or string identifier.

    Returns:
        Matching ``ArchitectureProfile``.

    Raises:
        ValueError: If the architecture ID is unknown.
    """
    if isinstance(architecture_id, str):
        try:
            architecture_id = ArchitectureId(architecture_id)
        except ValueError as exc:
            raise ValueError(f"Unknown architecture ID: {architecture_id}") from exc

    profile = ARCHITECTURE_CATALOG.get(architecture_id)
    if profile is None:
        raise ValueError(f"Unknown architecture ID: {architecture_id}")
    return profile


def list_architectures() -> List[ArchitectureProfile]:
    """Return all registered architecture profiles."""
    return list(ARCHITECTURE_CATALOG.values())
