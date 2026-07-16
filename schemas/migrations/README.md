# Schema migrations

Migrations are append-only compatibility records. Published Atlas Release bytes
are never rewritten by a migration; a reader either supports the declared
schema version or rejects the package as unsupported.
