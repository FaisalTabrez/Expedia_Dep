# Conformance tests

Cross-adapter Query Core, SDK, REST, and plugin conformance tests.

M2.5 adds `test_m2_5_adapter_conformance.py`, which executes the same request
corpus through Core, the local Python SDK, and the local WSGI REST adapter. The
three result envelopes must be logically identical, including provenance,
warnings, errors, ordering, and cursor behavior.

M2.6 adds `test_m2_6_explorer_conformance.py`, which verifies that Explorer
consumes those Core-owned envelopes without adding query semantics and labels
canonical rows, provenance, evidence, typed errors, and absent derived content
explicitly.
