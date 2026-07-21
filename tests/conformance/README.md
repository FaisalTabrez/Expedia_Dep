# Conformance tests

Cross-adapter Query Core, SDK, REST, and plugin conformance tests.

M2.5 adds `test_m2_5_adapter_conformance.py`, which executes the same request
corpus through Core, the local Python SDK, and the local WSGI REST adapter. The
three result envelopes must be logically identical, including provenance,
warnings, errors, ordering, and cursor behavior.
