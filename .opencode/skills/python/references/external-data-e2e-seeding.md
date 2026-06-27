# External-data E2E seeding pattern

Use this when adding a Python seed/backfill path that can run either against paid/authenticated provider APIs or deterministic local fixtures.

## Pattern

- Put provider I/O behind explicit source modes, for example `--source fixtures|provider` and `--weather-source fixtures|provider`.
- Auto-detect keys only for convenience when the caller did not explicitly request a real provider.
- If the caller explicitly requests a real provider and the required key/dependency is absent, fail loud with the exact missing env var or package extra. Do not silently fall back to fixtures.
- Make fixture mode deterministic and useful as an end-to-end smoke path, not a toy unit fixture.
- Write through the same catalog/storage interface as real data so the smoke verifies serialization, schema, readers, and API summaries.
- Guard dangerous defaults: reject empty catalog/output paths before globbing or writing, because shell expansion mistakes can otherwise scan or write the current directory.
- Return/write a concise JSON summary with `ok`, total records written, and counts by event type/table.

## Minimal CLI shape

```bash
uv run python scripts/seed_catalog.py \
  --catalog-path "$CATALOG_PATH" \
  --source fixtures \
  --weather-source fixtures \
  --start-date 2026-06-01 \
  --hours 2
```

For real providers:

```bash
export PROVIDER_API_KEY='...'
uv sync --extra real-data
uv run python scripts/seed_catalog.py \
  --catalog-path "$CATALOG_PATH" \
  --source provider \
  --hours 24
```

## Verification

- Run focused lint on the new module, tests, and wrapper script.
- Run the project test suite or the repo's CI-equivalent pytest command.
- Run a fixture smoke and read back with the public catalog/API reader, not just by checking files exist.
- If real keys are unavailable, report the exact command to run once keys are present; do not claim real-provider verification.

## Useful assertions

- Explicit real source without env key raises a clear error.
- Explicit real source without optional dependency raises a clear error naming the extra to install.
- Fixture source writes all expected event/table types.
- Empty `--catalog-path` / output path is rejected.
