# ADR-010: trusted local release read boundary

**Status:** Proposed — pending maintainer acceptance for M2.
**EDS register decision:** SDK and REST are thin adapters over Query Core.

## Decision

Query Core SHALL accept a release for trusted query execution only through the
local Release Reader verification boundary. That boundary SHALL verify the
ReleaseManifest, every manifest-addressed artifact digest and size, packaged
schema compatibility, and safe artifact paths before Query Core exposes records,
vectors, or derived artifacts as trusted data.

SDK and REST SHALL remain thin adapters over Query Core. They SHALL NOT open
release payloads, evaluate artifact trust, implement ranking/filtering semantics,
or construct trusted query results independently. A failed verification MAY
expose diagnostic manifest metadata only; it SHALL NOT produce trusted Atlas
records, vectors, or similarity results.

This decision defines a local library boundary only. It does not select a remote
deployment, access-control model, signature trust root, archive service, or
new release state.

## Rationale

EDS section 15.3 requires verification before trusted operation, while sections
11 and 12 require a local reference read path and one semantic authority. Using
the existing Release Reader as the only trusted-release entry point prevents an
SDK, REST adapter, or Explorer client from treating a mutable workspace or an
unverified package as an Atlas Release.

## Consequences

- Query Core depends on a verified-release handle, not arbitrary file paths or
  Builder workspaces.
- The M1 Draft fixture may support local M2 conformance only after Reader
  verification; this does not alter its Draft, licensing, or citation state.
- Signature-policy and remote-service concerns remain deferred under OQ-10 and
  OQ-07. Digest and schema verification remain mandatory in M2.
- SDK, REST, and Explorer implementations are simplified: they consume Core
  contracts and cannot become competing release readers.

## Acceptance criteria

1. A changed manifest-addressed artifact, unsafe path, missing artifact, or
   incompatible packaged schema causes trusted release opening to fail.
2. Query Core never returns a trusted record, vector, or similarity result from
   a failed verification result.
3. SDK and REST conformance tests show that their release context is obtained
   from Query Core rather than from independent package parsing.
4. A local verified package can be queried without a service dependency.

## EDS clauses affected

- EDS 5 architecture and dependency direction
- EDS 11, especially local SDK/REST behavior
- EDS 12 execution model and local-library-first strategy
- EDS 15.3 local trust and supply-chain model
- ERS REQ-015 and REQ-021

## Non-goals

This draft does not authorize a new reader format, signature policy, remote
catalog, service deployment, or mutation of any Atlas Release.
