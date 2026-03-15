"""
Quick smoke test — runs the graph with a minimal state
and prints the final report. No LLM calls, no DB needed.
"""

# Import external libraries
import os
import sys

# Ensuring project root is on PATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Internal Packages
from agent.graph import compliance_graph
from config.logging import setup_logging

# Setup logging
setup_logging()


def main():
    # Read non-compliant fixture contract
    contract_text = open("tests/fixtures/contracts/contract_non_compliant.md").read()

    initial_state = {
        "contract_id": "test-001",
        "filename": "contract_non_compliant.md",
        "raw_text": open("tests/fixtures/contracts/contract_non_compliant.md").read(),
        "clauses": [],
        "policy_chunks": [],
        "web_results": [],
        "findings": [],
        "drafted_clauses": [],
        "report": None,
        "error": None,
        "retry_count": 0,
    }

    print("\n🚀 Running compliance graph...\n")

    # invoke() runs the graph synchronously — perfect for testing
    final_state = compliance_graph.invoke(initial_state)  # type: ignore

    # Guard against failed runs where report didn't generate
    report = final_state.get("report")
    if not report:
        print("\n❌ Graph failed to generate report")
        print(f"     Last error: {final_state.get("error", "Unknown")}")
        print(f"     Retry count: {final_state.get('retry_count', 0)}")
        return

    # print("\n✅ Graph completed successfully")
    # print(f"   Contract ID  : {final_state["report"]["contract_id"]}")
    # print(f"   Filename     : {final_state["report"]["filename"]}")
    # print(f"   Total clauses: {final_state["report"]["total_clauses"]}")
    # print(f"   Findings     : {final_state["report"]['non_compliant_clauses']}")
    # print(f"   Status       : {final_state["report"]["status"]}")

    # Display parsed clauses
    print("\n Parsed clauses")
    for clause in final_state.get("clauses", []):
        print(f">>> [{clause["clause_id"]}] {clause["title"]}")

    # Show findings with drafted replacements
    findings = final_state.get("findings", [])
    if findings:
        print(f"\n>>> Compliance Findings ({len(findings)}):")
        for f in findings:
            print(f"\n  [{f['severity']}] {f['clause_id']} → {f['policy_id']}")
            print(f"    Reason  : {f['reason']}")
            if f.get("suggested_text"):
                print(f"    Fix     : {f['suggested_text'][:120]}...")

    else:
        print("\n No compliance violations found.")

    # Show summary
    summary = report.get("summary", {})
    print(f"\n Summary:")
    print(f">>> Overall status : {summary.get('overall_status')}")
    print(f">>> Total clauses  : {summary.get('total_clauses')}")
    print(f">>> Non-compliant  : {summary.get('non_compliant_clauses')}")
    print(
        f">>> HIGH findings  : {summary.get('severity_breakdown', {}).get('HIGH', 0)}"
    )
    print(
        f">>> MEDIUM findings: {summary.get('severity_breakdown', {}).get('MEDIUM', 0)}"
    )


if __name__ == "__main__":
    main()
