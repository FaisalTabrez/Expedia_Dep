"""JSON Schema conformance fixtures for the enforced contract packs."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from referencing import Registry, Resource
except ImportError:  # pragma: no cover - exercised only without the locked test group.
    Draft202012Validator = None  # type: ignore[assignment,misc]
    FormatChecker = None  # type: ignore[assignment,misc]
    Registry = None  # type: ignore[assignment,misc]
    Resource = None  # type: ignore[assignment,misc]


ROOT = Path(__file__).resolve().parents[2]


@unittest.skipIf(Draft202012Validator is None, "run with: uv run --group test python -m unittest")
class JsonSchemaConformanceTests(unittest.TestCase):
    def _fixture_pack(self, kind: str, pack: str) -> dict[str, object]:
        path = ROOT / "fixtures" / kind / pack
        return json.loads(path.read_text())

    def _errors(self, schema_path: str, instance: object) -> list[object]:
        schema = json.loads((ROOT / schema_path).read_text())
        registry = Registry()
        for path in (ROOT / "schemas" / "json").glob("*.schema.json"):
            candidate = json.loads(path.read_text())
            registry = registry.with_resource(candidate["$id"], Resource.from_contents(candidate))
        validator = Draft202012Validator(schema, format_checker=FormatChecker(), registry=registry)
        return list(validator.iter_errors(instance))

    def test_every_positive_contract_fixture_conforms(self) -> None:
        for pack in ("m1-contract-pack.json", "m2-query-contract-pack.json"):
            fixture_pack = self._fixture_pack("valid", pack)
            for fixture in fixture_pack["fixtures"]:  # type: ignore[index]
                with self.subTest(pack=pack, contract=fixture["contract"]):  # type: ignore[index]
                    self.assertEqual([], self._errors(fixture["schema"], fixture["instance"]))  # type: ignore[index]

    def test_every_negative_contract_fixture_is_rejected(self) -> None:
        for pack in ("m1-contract-pack.json", "m2-query-contract-pack.json"):
            fixture_pack = self._fixture_pack("invalid", pack)
            for fixture in fixture_pack["fixtures"]:  # type: ignore[index]
                with self.subTest(pack=pack, name=fixture["name"]):  # type: ignore[index]
                    self.assertNotEqual([], self._errors(fixture["schema"], fixture["instance"]))  # type: ignore[index]

    def test_schema_catalogue_has_draft_2020_12_identifiers(self) -> None:
        for schema_path in (ROOT / "schemas" / "json").glob("*.schema.json"):
            schema = json.loads(schema_path.read_text())
            with self.subTest(schema=schema_path.name):
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
                self.assertTrue(schema["$id"].startswith("https://expedia.dev/schemas/json/"))


if __name__ == "__main__":
    unittest.main()
