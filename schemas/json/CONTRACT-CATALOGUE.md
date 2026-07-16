# EXPEDIA JSON contract catalogue

**Governing specification:** EDS v2.1 Appendix A  
**Schema dialect:** JSON Schema Draft 2020-12  
**Compatibility policy:** contract versions are immutable once used by a Draft
release. Consumers reject undeclared fields in canonical objects.

## M1 contract pack

| Contract | Owner | First enforcement | M1 fixture coverage |
|---|---|---:|---|
| `release-manifest` | Storage / release packaging | M1.6 | Valid, malformed artifact, non-string digest |
| `genome-record-version` | Atlas Builder | M1.4 | Valid, undeclared runtime field |
| `atlas-entity` | Atlas Builder | M1.4 | Valid |
| `source-provenance` | Atlas Builder | M1.3 | Valid, invalid timestamp |
| `embedding-profile` | Profiles / Atlas Builder | M1.5 | Valid, missing model digest |
| `embedding-instance` | Atlas Builder | M1.5 | Valid |
| `build-manifest` | Atlas Builder | M1.3 | Valid |
| `stage-envelope` | Atlas Builder | M1.3 | Valid |
| `validation-bundle` | Validation | M1.7 | Valid |
| `approval-record` | Release governance | M1.8 | Valid |
| `waiver-record` | Release governance | M1.7 | Valid |
| `vector-shard-manifest` | Atlas Builder | M1.5 | Valid |
| `plugin-descriptor` | Profiles / Atlas Builder | M1.5 | Covered by M1.1 descriptor tests |

The executable M1 fixture packs are
`fixtures/valid/m1-contract-pack.json` and
`fixtures/invalid/m1-contract-pack.json`. Run them through the locked test
group with `uv run --group test python -m unittest discover -s tests/contract`.

## Deferred contracts

The following schemas establish EDS names and structural boundaries but are not
behaviorally implemented or fixture-enforced in M1: `annotation-assertion`,
`derived-relation`, `query-request`, and `query-result`. Query contracts remain
M2 work; their presence here must not be read as a Query Core implementation.

`contract-meta` is a shared metadata schema, referenced where a contract
envelope elects to carry contract metadata.
