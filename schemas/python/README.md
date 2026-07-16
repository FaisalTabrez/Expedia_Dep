# Python contract bindings

This package provides dependency-free, immutable bindings for the initial
canonical JSON contracts. The JSON Schema files in `../json/` remain normative;
these bindings enforce their currently supported structure and provide canonical
JSON serialization for Python callers.

Run the dependency-free contract suite with:

```powershell
python -m unittest discover -s tests/contract -p 'test_*.py' -v
```
