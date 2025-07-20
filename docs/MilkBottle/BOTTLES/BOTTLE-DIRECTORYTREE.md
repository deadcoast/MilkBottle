# Milk Bottle Directory Tree

```plaintext
milkbottle/
├── pyproject.toml
├── README.md
├── TASKLIST.md               # master tracker
├── milkbottle.toml           # global defaults
├── src/
│   └── milkbottle/
│       ├── __init__.py
│       ├── MilkBottle.py     # root Typer command (`milk`)
│       ├── registry.py       # bottle discovery / alias map
│       ├── config.py         # load+merge settings
│       ├── utils.py          # shared helpers (slugify, rich console…)
│       ├── errors.py         # MilkBottleError hierarchy
│       └── modules/
│           ├── __init__.py
│           └── pdfmilker/
│               ├── __init__.py
│               ├── cli.py
│               ├── discovery.py
│               ├── prepare.py
│               ├── extract.py
│               ├── transform.py
│               ├── validate.py
│               ├── relocate.py
│               ├── report.py
│               ├── utils.py
│               └── errors.py
├── tests/
│   ├── __init__.py
│   ├── test_milkbottle_cli.py
│   ├── test_registry.py
│   ├── test_config.py
│   └── pdfmilker/
│       ├── test_discovery.py
│       ├── test_prepare.py
│       ├── test_extract.py
│       ├── test_transform.py
│       ├── test_validate.py
│       ├── test_relocate.py
│       └── test_report.py
├── .gitignore
└── .editorconfig
```
