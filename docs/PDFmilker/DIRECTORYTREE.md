# DIRECTORY TREE

```
pdfmilker/
├── pyproject.toml
├── README.md
├── scratchpad.md            # task tracker (already created)
├── pdfmilker.toml           # user-editable defaults
├── src/
│   └── pdfmilker/
│       ├── __init__.py
│       ├── cli.py           # Typer app + interactive menu
│       ├── discovery.py     # Step 1
│       ├── prepare.py       # Step 2
│       ├── extract.py       # Step 3
│       ├── transform.py     # Step 4
│       ├── validate.py      # Step 5
│       ├── relocate.py      # Step 6
│       ├── report.py        # Step 7
│       ├── utils.py         # shared helpers
│       └── errors.py        # custom exceptions
├── tests/
│   ├── __init__.py
│   ├── test_discovery.py
│   ├── test_prepare.py
│   ├── test_extract.py
│   ├── test_transform.py
│   ├── test_validate.py
│   ├── test_relocate.py
│   └── test_report.py
├── .gitignore
└── .editorconfig
```
