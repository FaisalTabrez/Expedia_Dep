# Validation

M1.7 provides an independent Draft-package reader. It consumes only the package
directory and the schemas embedded in that package; it does not read Builder
workspaces, model snapshots, or original acquisition inputs.

Run it from a clean working directory with the committed reader source and the
pinned test dependency (`jsonschema==4.23.0`):

```powershell
$env:PYTHONPATH = (Resolve-Path "validation\src")
python -m expedia_validation.release_reader `
  --package C:\clean-room\expedia-m1-draft-20260721-v2 `
  --validation-bundle C:\clean-room\evidence\validation-bundle.json `
  --run-record C:\clean-room\evidence\clean-room-run.json `
  --bundle-id m1-draft-20260721-v2-clean-room-v1 `
  --environment-label independent-clean-room-v1
```

The ValidationBundle is external evidence bound to the ReleaseManifest digest.
It is not inserted into the already frozen Draft package, which avoids a
self-referential manifest/bundle digest cycle. M1.8—not M1.7—records the
maintainer approval or rejection.
