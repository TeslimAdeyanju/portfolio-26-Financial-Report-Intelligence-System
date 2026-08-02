# Development workspace

This directory contains files needed to develop and verify FRIS, but not to run the
application in production.

```text
development/
├── requirements.txt     # Test and development dependencies
├── tests/               # Automated tests
└── tools/               # Future maintenance and developer scripts
```

From the repository root:

```bash
python -m pip install -r development/requirements.txt
pytest
```
