"""JSON Schema conformance fixtures for the M1 contract pack."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # pragma: no cover - exercised only without the locked test group.
    Draft202012Validator = None  # type: ignore[assignment,misc]
    FormatChecker = None  # type: ignore[assignment,misc]


ROOT = Path(__file__).resolve().parents[2]


@unittest.skipIf(Draft202012Validator is None, "run with: uv run --group test python -m unittest")
class JsonSchemaConformanceTests(unittest.TestCase):
    def _fixture_pack(self, kind: str) -> dict[str, object]:
        path = ROOT / "fixtures" / kind / "m1-contract-pack.json"
        return json.loads(path.read_text())

    def _errors(self, schema_path: str, instance: object) -> list[object]:
        schema = json.loads((ROOT / schema_path).read_text())
        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        return list(validator.iter_errors(instance))

    def test_every_positive_m1_contract_fixture_conforms(self) -> None:
        fixture_pack = self._fixture_pack("valid")
        for fixture in fixture_pack["fixtures"]:  # type: ignore[index]
            with self.subTest(contract=fixture["contract"]):  # type: ignore[index]
                self.assertEqual([], self._errors(fixture["schema"], fixture["instance"]))  # type: ignore[index]

    def test_every_negative_m1_contract_fixture_is_rejected(self) -> None:
        fixture_pack = self._fixture_pack("invalid")
        for fixture in fixture_pack["fixtures"]:  # type: ignore[index]
            with self.subTest(name=fixture["name"]):  # type: ignore[index]
                self.assertNotEqual([], self._errors(fixture["schema"], fixture["instance"]))  # type: ignore[index]

    def test_schema_catalogue_has_draft_2020_12_identifiers(self) -> None:
        for schema_path in (ROOT / "schemas" / "json").glob("*.schema.json"):
            schema = json.loads(schema_path.read_text())
            with self.subTest(schema=schema_path.name):
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
                self.assertTrue(schema["$id"].startswith("https://expedia.dev/schemas/json/"))


if __name__ == "__main__":
    unittest.main()
