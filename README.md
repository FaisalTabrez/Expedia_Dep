# EXPEDIA

EXPEDIA is open scientific infrastructure for constructing, validating,
publishing, querying, and exploring versioned genomic embedding atlases.

The canonical scientific object is an immutable Atlas Release. The Atlas
Builder produces releases; Query Core owns read-only query semantics; Explorer,
SDK, and REST are clients. The EDS v2.1 and ERS v1.0 source documents in this
repository govern implementation.

## Repository layout

The top-level subsystem layout follows EDS v2.1 section 16. `schemas/` is the
normative contract source; generated types and client bindings must never
redefine its semantics. M1 implements the Builder reference path, Draft-package
reader, and evidence gate. Query Core, SDK, REST, Explorer, storage services,
and UI behavior remain planned M2-or-later work.

See [the M1 implementation plan](docs/planning/M1-IMPLEMENTATION-PLAN.md) for
the completed M1 evidence path and [the M2 implementation plan](docs/planning/M2-IMPLEMENTATION-PLAN.md)
for the next gated work.
