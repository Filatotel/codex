# Validation Tools

Run `python tools/validate_structure.py` for the lightweight deterministic Wave-1 structure gate. It checks root/engine references, role shape, schema syntax, bounded skill namespaces, duplicate active skill IDs, optional-pattern classification, and preservation/removal of key legacy runtime surfaces.

`python -m unittest tests.test_structure` wraps the same gate for standard-library test runners. No external orchestration framework is required.
