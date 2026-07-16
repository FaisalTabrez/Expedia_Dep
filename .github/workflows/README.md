# CI workflow placeholders

No executable CI workflow is enabled by the skeleton. When implementation
starts, workflows in this directory must implement the EDS section 16 gates:

1. schema compatibility and contract-fixture validation;
2. Builder-stage positive and negative tests;
3. Query Core/SDK/REST conformance (M2 onward);
4. manifest, checksum, source-provenance, and license checks;
5. benchmark-preregistration validation; and
6. documentation/ERS/ADR consistency checks.

Workflows must run against pinned environments and retain the resulting
evidence links. They must not embed secrets in release manifests.
