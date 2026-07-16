# JSON Schema contracts

All schemas use JSON Schema Draft 2020-12 and carry a stable `contract_id` and
semantic `contract_version`. `additionalProperties: false` is intentional for
canonical objects: plugins and clients must not introduce undeclared fields.
