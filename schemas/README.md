# Contract schemas

`schemas/` is the normative source for versioned machine-readable contracts.
JSON Schema is used for manifests, profiles, governance records, and API value
objects. Arrow and Parquet schema definitions will govern release tables;
generated language bindings are derived artifacts.

Every schema change requires a compatibility decision, migration guidance when
needed, and positive and negative fixtures. Schema files in this skeleton define
structure only; they do not authorize a release or implement behavior.
