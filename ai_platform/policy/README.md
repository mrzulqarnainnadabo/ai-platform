# Policy Boundary

Policy is deterministic and provider-neutral. The application supplies trusted identity and permissions; the platform evaluates the requested capability.

Decisions are `ALLOW`, `DENY`, and `REQUIRE_HUMAN`. Unknown capabilities, malformed authorization context, and evaluator failures fail closed. Model output is never an authority source.
