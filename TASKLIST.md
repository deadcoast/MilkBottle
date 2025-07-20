# TASKLIST.md

## Wire up the pipeline:

MAJOR COMPLETION TASKS:

- [x] Discovers PDFs
- [x] Prepares output directories
- [x] Extracts text/images/metadata
- [x] Transforms to Markdown
- [x] Validates assets
- [x] Relocates the PDF
- [x] Integrate the pipeline with the CLI

---

- [x] **End-to-End Pipeline Integration**

  - [x] Implement a function that runs the full PDFmilker pipeline (discover → prepare → extract → transform → validate → relocate → report) for all PDFs in the target directory.
  - [x] Integrate this pipeline with the PDFmilker CLI menu so that "Start PDF Extraction Process" actually runs the workflow.
  - [x] Add error handling and logging for the full pipeline.

- [x] **User-Facing CLI Improvements**

  - [x] Make CLI options (`--outdir`, `--overwrite`, `--images/--no-images`, `--log-level`, `--pattern`) actually control the pipeline.
  - [x] Add progress bars (tqdm) and Rich status updates for batch operations.
  - [x] Ensure all CLI help and error messages are clear and user-friendly.

- [x] **Error Handling & Logging**

  - [x] Ensure all exceptions are caught and logged with useful messages.
  - [x] Write structured logs to `/meta/<slug>.log` in JSONL format.

- [x] **Configuration**

  - [x] Make sure all config options (TOML, env, CLI) are respected throughout the pipeline.
  - [x] Add support for `pdfmilker.toml` and CLI overrides.

- [x] **Extensibility**

  - [x] Document and test the entry-point/plugin system for adding new bottles.
  - [x] Provide a template or example for a new bottle.

- [ ] **Testing suite**

  - [ ] Write unit tests for each pipeline step (discovery, prepare, extract, transform, validate, relocate, report).
  - [ ] Write integration tests for the full pipeline.
  - [ ] Write CLI tests (simulate user input, check outputs).
  - [ ] Achieve 90%+ test coverage.
  - [ ] Unit tests for CLI root & registry
  - [ ] Unit tests for each PDFmilker SRP module
  - [ ] End‑to‑end extraction fixture tests

- [ ] **Documentation**
  - [ ] Update README.md with real usage examples and troubleshooting.
  - [ ] Document how to add new bottles/plugins.
  - [ ] Document configuration and environment setup.
  - [ ] Keep TASKLIST.md up to date.
