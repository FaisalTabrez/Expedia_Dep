# JSON Schema contracts

All schemas use JSON Schema Draft 2020-12 and carry a stable `$id` with a
semantic contract version. `additionalProperties: false` is intentional for
canonical objects: plugins and clients must not introduce undeclared fields.

`CONTRACT-CATALOGUE.md` identifies the owning subsystem, first enforcement
milestone, and M1 conformance-fixture coverage for every schema.
