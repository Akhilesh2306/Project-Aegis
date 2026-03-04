"""File to manage the state of the agent"""

# Import External Libraries
import operator
from typing import Annotated, Optional
from typing_extensions import TypedDict


class Clause(TypedDict):
    """A single parsed clause from contract"""

    clause_id: str
    section_number: str
    title: str
    content: str


class PolicyChunk(TypedDict):
    """A retrieved chunk from the policy document"""

    policy_id: str
    title: str
    content: str
    relevance_score: float


class Finding(TypedDict):
    """A single compliance violation found by the agent"""

    clause_id: str
    policy_id: str
    severity: str
    reason: str
    current_text: str


class DraftedClause(TypedDict):
    """A remediated version of a non-compliant clause"""

    clause_id: str
    original_text: str
    suggested_text: str
    changes_summary: str


class ComplianceState(TypedDict):
    """Every node reads from and writes to this state"""

    # === Input ===
    contract_id: str
    filename: str
    raw_text: str

    # === Processing ===
    clauses: Annotated[list[Clause], operator.add]
    policy_chunks: Annotated[list[PolicyChunk], operator.add]
    web_results: Annotated[list[str], operator.add]

    # === Agent Output ===
    findings: Annotated[list[Finding], operator.add]
    drafted_clauses: Annotated[list[DraftedClause], operator.add]

    # === Final Report ===
    report: Optional[dict]

    # === Control Flow ===
    error: Optional[str]
    retry_count: int
