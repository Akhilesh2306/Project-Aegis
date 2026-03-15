"""File for clause drafting node"""

# Import External Libraries
import yaml
import logging
from pathlib import Path
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.messages import SystemMessage, HumanMessage

# Import Internal Packages
from config.settings import get_settings
from agent.state import ComplianceState, DraftedClause, Finding

# Setup logging and settings
settings = get_settings()
logger = logging.getLogger(__name__)


# =========================
# Clause Drafting Node
# =========================
def clause_drafting_node(state: ComplianceState) -> dict:
    """
    Generates compliant replacement text for each finding.
    Reads: findings, clauses, policy_chunks
    Writes: drafted_clauses
    """
    findings = state.get("findings", [])

    if not findings:
        logger.info("[clause_drafting] No findings found in state - skipping")
        return {"drafted_clauses": []}

    logger.info(f"[clause_drafting] Drafting fixes for {len(findings)} findings")

    try:
        prompt = _load_prompt()
        llm = _build_llm()

        system_msg = SystemMessage(content=prompt["system"])
        user_content = prompt["user"].format(
            policies=_format_policies(state),
            findings_with_context=_format_findings_with_context(findings, state),
        )
        human_msg = HumanMessage(content=user_content)

        logger.info("[clause_drafting] Calling LLM...")

        structured_llm = llm.with_structured_output(DraftedClausesSchema)
        result: DraftedClausesSchema = structured_llm.invoke([system_msg, human_msg])  # type: ignore

        drafted_clauses: list[DraftedClause] = [
            {
                "clause_id": d.clause_id,
                "original_text": d.original_text,
                "suggested_text": d.suggested_text,
                "changes_summary": d.changes_summary,
            }
            for d in result.drafted_clauses
        ]

        logger.info(f"[clause_drafting] Drafted {len(drafted_clauses)} clauses")

        for draft in drafted_clauses:
            logger.info(
                f"[clause_drafting] -> {draft['clause_id']}: {draft['changes_summary']}"
            )

        return {
            "drafted_clauses": drafted_clauses,
        }

    except Exception as e:
        logger.error(f"[clause_drafting] LLM call failed: {e}")
        return {
            "drafted_clauses": [],
            "error": f"Clause drafting failed: {str(e)}",
        }


# =========================
# Prompt loading
# =========================s
def _load_prompt() -> dict:
    """
    Load prompt templates from YAML file.
    """
    prompt_path = Path(__file__).parent.parent / "prompts" / "clause_drafting.yaml"

    with open(prompt_path) as f:
        return yaml.safe_load(f)


# =========================
# LLM Setup
# =========================
def _build_llm() -> ChatOpenAI:
    """
    Creates an LLM instance for compliance checking.
    """

    return ChatOpenAI(
        model=settings.openai_model,
        api_key=settings.openai_api_key,  # type: ignore
        temperature=0.1,  # slight creativity for natural language
        max_completion_tokens=settings.drafting_max_tokens,
    )


# =========================
# Context Formatters
# =========================
def _format_findings_with_context(
    findings: list[Finding],
    state: ComplianceState,
) -> str:
    """
    Builds rich context block for each finding - includes the original clause text so the LLM knows exactly what to rewrite.
    """
    clauses_by_id = {c["clause_id"]: c for c in state.get("clauses", [])}

    lines = []
    for i, finding in enumerate(findings, 1):
        clause = clauses_by_id.get(finding["clause_id"], {})
        lines.append(
            f"Finding #{i}:\n"
            f"- Clause ID   : {finding["clause_id"]}\n"
            f"- Policy ID   : {finding["policy_id"]}\n"
            f"- Severity    : {finding["severity"]}\n"
            f"- Reason      : {finding["reason"]}\n"
            f"- Current Text: {clause.get("content", finding["current_text"])}\n"
        )

    return "\n\n".join(lines)


def _format_policies(state: ComplianceState) -> str:
    """
    Formats retrieved policy chunks into readable text for the prompt.
    """
    chunks = state.get("policy_chunks", [])
    if not chunks:
        return "No specific policies retrieved."

    lines = []
    for chunk in chunks:
        lines.append(f"[{chunk["policy_id"]}] {chunk["title"]}\n{chunk["content"]}")

    return "\n\n".join(lines)


# =========================
# Structured Output Schema
# =========================
class DraftedClauseSchema(BaseModel):
    """
    Pydantic model for single drafted clause.
    """

    clause_id: str
    original_text: str
    suggested_text: str
    changes_summary: str


class DraftedClausesSchema(BaseModel):
    """
    Wrapper for multiple drafted clauses.
    """

    drafted_clauses: list[DraftedClauseSchema]
