"""File for compliance check node"""

# Import External Libraries
import yaml
import logging
from pathlib import Path
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.messages import HumanMessage, SystemMessage

# Import Internal Packages
from config.settings import get_settings
from agent.state import ComplianceState, Finding

# Setup logging and settings
settings = get_settings()
logger = logging.getLogger(__name__)


# =========================
# Compliance Check Node
# =========================
def compliance_check_node(state: ComplianceState) -> dict:
    """
    Core ReAct agent - analyses clauses against policies and produces a list of findings.
    Reads: clauses, policy_chunks
    Writes: findings
    """

    clauses = state.get("clauses", [])
    if not clauses:
        logger.warning("[compliance_check] No clauses found in state - skipping")
        return {"findings": []}

    logger.info(
        f"[compliance_check] Analysing {len(clauses)} clauses against {len(state.get('policy_chunks', []))} policy chunks..."
    )

    try:
        prompt = _load_prompt()
        llm = _build_llm()

        # Build the messages
        system_msg = SystemMessage(content=prompt["system"])
        user_content = prompt["user"].format(
            contract_value="120,000",
            policies=_format_policies(state),
            clauses=_format_clauses(state),
        )
        human_msg = HumanMessage(content=user_content)

        logger.info("[compliance_check] Calling LLM...")

        # Use structured output - enforces FindingSchema response
        structured_llm = llm.with_structured_output(FindingsSchema)
        result: FindingsSchema = structured_llm.invoke([system_msg, human_msg])  # type: ignore

        # Convert Pydantic models to Finding TypedDicts
        findings: list[Finding] = [
            {
                "clause_id": f.clause_id,
                "policy_id": f.policy_id,
                "severity": f.severity,
                "reason": f.reason,
                "current_text": f.current_text,
            }
            for f in result.findings
        ]

        # Log each finding clearly
        logger.info(f"[compliance_check] Found {len(findings)} violations")
        for finding in findings:
            logger.info(
                f"[compliance_check]   ⚠️  [{finding['severity']}] "
                f"{finding['clause_id']} violates {finding['policy_id']}: "
                f"{finding['reason']}"
            )

        return {"findings": findings}

    except Exception as e:
        logger.error(f"[compliance_check] LLM call failed: {e}")
        return {
            "findings": [],
            "error": f"Compliance check failed: {str(e)}",
        }


# =========================
# Prompt loading
# =========================
def _load_prompt() -> dict:
    """
    Load prompt templates from YAML file.
    """
    prompt_path = Path(__file__).parent.parent / "prompts" / "compliance_check.yaml"

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
        temperature=0,  # deterministic - compliance needs consistency, no randomness
        max_completion_tokens=settings.compliance_check_max_tokens,
    )


# =========================
# Context Formatters
# =========================
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


def _format_clauses(state: ComplianceState) -> str:
    """
    Formats parsed clauses into readable text for the prompt.
    """
    clauses = state.get("clauses", [])
    if not clauses:
        return "No clauses provided."

    lines = []
    for clause in clauses:
        lines.append(f"[{clause["clause_id"]}] {clause["title"]}\n{clause["content"]}")

    return "\n\n".join(lines)


# =========================
# Structured Output Schema
# =========================
class FindingSchema(BaseModel):
    """
    Pydantic model for single compliance finding.
    """

    clause_id: str
    policy_id: str
    severity: str
    reason: str
    current_text: str


class FindingsSchema(BaseModel):
    """
    Wrapper for list of findings
    """

    findings: list[FindingSchema]
