# Violation Legend — Non-Compliant Contract

This file maps every known violation in `contract_non_compliant.md`
to the policy it breaches. Use this as ground truth when verifying
agent output during development and testing.

| Section   | Policy                   | Requirement                 | Actual          | Severity |
| --------- | ------------------------ | --------------------------- | --------------- | -------- |
| Section 2 | P-001 Termination Notice | Minimum 90 days             | 30 days         | HIGH     |
| Section 3 | P-002 Liability Cap      | Max 2x annual value ($240k) | Unlimited       | HIGH     |
| Section 4 | P-005 Payment Terms      | Net-30                      | Net-60          | MEDIUM   |
| Section 5 | P-004 Dispute Resolution | Arbitration required        | Litigation only | HIGH     |
| Section 6 | P-003 Data Privacy       | GDPR or CCPA reference      | Missing         | HIGH     |

## Expected Agent Output

- Total clauses analysed: 7
- Non-compliant clauses: 5
- Compliant clauses: 2 (Section 1 Services, Section 7 Confidentiality)

## How to use this file

When the agent processes `contract_non_compliant.md`, its findings
should match this table exactly. Any missing finding is a recall
error. Any extra finding is a hallucination. Both need investigation.
