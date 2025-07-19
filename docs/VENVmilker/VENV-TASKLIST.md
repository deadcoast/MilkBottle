# VENVmilker — Code Generation Tasklist

- [ ] **Task 1 – Scaffold package structure**

  - [ ] Create `src/milkbottle/modules/venvmilker/__init__.py` with version & `get_cli()`
  - [ ] Add `cli.py` Typer app skeleton and default command

- [ ] **Task 2 – Implement core workflow stubs**

  - [ ] Draft `workflow.py` with Detect ➜ Create ➜ Activate placeholders
  - [ ] Add supporting `config.py`, `errors.py`, and `utils.py` minimal logic

- [ ] **Task 3 – Flesh out functional workflow**

  - [ ] Complete `create_venv`, `install_packages`, `snapshot_requirements`, and hash‑dedupe logic in `workflow.py`.
  - [ ] Finalize CLI flag handling & default path in `cli.py`.

- [ ] **Task 4 – Cross‑platform activation & shell support**

  - [ ] Implement `activate_environment()` for bash/zsh/fish/PowerShell.
  - [ ] Add graceful fallback messages when shell isn’t supported.

- [ ] **Task 5 – Test suite**

  - [ ] Write unit tests for detect/create/activate logic.
  - [ ] Set up pytest coverage & GitHub Actions matrix (macOS, Windows).

- [ ] **Task 6 – Test suite**

  - [ ] Write unit tests for detect/create/activate logic.
  - [ ] Set up pytest coverage & GitHub Actions matrix (macOS, Windows).

- [ ] **Task 7 – Add entry‑point wiring**

  - [ ] Register bottle entry‑point in `pyproject.toml` and verify import.

- [ ] **Task 8 – Add tests & entry‑point wiring**
  - [ ] Write smoke tests in `tests/modules/venvmilker/`
  - [ ] Register bottle entry‑point in `pyproject.toml` and verify import
