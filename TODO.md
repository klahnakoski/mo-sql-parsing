# TODO

Known work in this repo. Each item names the test or file that proves it.

## Unimplemented grammar

These tests are `@skip("does not pass yet")` and their `expected` is still a placeholder `{}` —
unskipping means deciding the parse tree shape as well as writing the grammar.

- **`ADD JAR` / `JARS` / `FILE` / `FILES` / `ARCHIVE` / `ARCHIVES`** (Hive resource commands) —
  `tests/test_sqlglot.py` `test_issue_46_sqlglot_2` through `_7`. Six tests, one grammar rule.
- **`SHOW TABLES`** — `tests/test_sqlglot.py:826` `test_issue_46_sqlglot_89`. No `SHOW` grammar exists at all.
- **`ALTER TYPE x RENAME TO y`** — `tests/test_sqlglot.py:765` `test_issue_46_sqlglot_79`.
  `alter` currently accepts only `{table} | {session}`.
- **`SET -v`** (bare flag, no `=`) — `tests/test_sqlglot.py:26` `test_issue_46_sqlglot_1`.
- **`DECLARE b, c INT;`** (multiple vars in one MySQL `DECLARE`) — `tests/test_mysql.py:1144`
  `test_multiple_vars_in_declare`. Expected tree is already written; only the grammar is missing.
- **BigQuery `UNNEST` without `FROM`** — `tests/test_bigquery.py:446` `test_issue_98_interval2`.
  Skip note asks "missing FROM?" — decide whether that SQL is even legal before writing the rule.

## Error messages

- **`select c1, c as 't' from T` reports the wrong error** — `tests/test_errors.py:78`
  `test_issue_88_parse_error`, marked "this test is correct, please fix". A single-quoted string
  where an alias belongs should say `Expecting identifier`.
- Error reporting generally is weak (the README has said so since version 7). The parser reports the
  deepest failed alternative, which is often not the one the user meant.

## Formatter

- **`_generator` is a stub** — `mo_sql_parsing/formatting.py:367`, `# TODO: replace with function-using-keywords`.
- **Round-trip coverage is not enforced.** `tests/test_bulk_sql_formatting.py:22`
  (`test_issue_46_sqlglot_{{num}}`) is skipped as "does not pass yet" and `:32` as "too long".
  There is no standing check that everything the parser accepts, the formatter can re-emit.

## Decisions to make

- **Double-quote warning default** — `mo_sql_parsing/utils.py:794`,
  `emit_warning_for_double_quotes`, `# NOT SURE IF True IS A GOOD DEFAULT`. Currently off for MySQL,
  on elsewhere. Either commit to a default or make it a `parse()` argument.

## Lazy-import fallout

- **`from mo_sql_parsing import sql_parser` returns `None` until a parse has happened.**
  `__init__.py` sets `sql_parser = _utils = ansi_string = scrub = None` at module scope, which shadows
  the real submodules; `_get_or_create_parser` rebinds them on first `parse()`. `tests/test_meta.py`
  relies on this (`_ensure_imported = sql_parser`) and so its import guard is silently dead. Either
  give the placeholders private names or drop the guard.

- **First parse costs ~470ms** — ~210ms importing submodules, ~260ms building the grammar — against
  ~1.5ms to then parse a statement. Each flavour (`common`/`mysql`/`sqlserver`/`bigquery`) pays the
  build again, since `lookup_parsers` keys on flavour.

  Nothing here is reducible from this repo, and the obvious ideas were measured and rejected — do not
  re-derive them:
  - ~130ms of the import half is `mo_dots`/`mo_future`, which `mo_parsing` pulls in itself.
  - The 260ms build has no hotspot in our code; it is `mo_parsing` constructing elements. Two
    candidate fixes there together moved 251ms to 246ms. Logged in `~/code/mo-parsing/TODO.md`.
  - A finalized parser cannot be pickled (`wrap_parse_action.<locals>.wrapper` is a local closure),
    so it cannot be cached to disk.
  - Sharing flavour-invariant subgrammars would need `literal_string`/`simple_ident` as `Forward`s
    rebound per parse. `finalize()` bakes first-character lookup tables that differ per flavour
    exactly there, so rebinding would mis-parse rather than fail. Not worth the risk.

## Build and packaging

- **`tests/requirements-3.8.lock` and `-3.9.lock` are unused.** `.github/workflows/build.yml` installs
  `tests/requirements.lock` at both lines 59 and 114, so the per-version locks never get exercised.
  Either wire the matrix to pick the right lock per Python version, or delete them.
- **CI does not test `dev`.** `build.yml` has `if: github.ref != 'refs/heads/dev'`, so the branch all
  work lands on is never built. Run the suite locally before merging to `master`.
- **README build badge points at Travis**, which the project no longer uses; CI is GitHub Actions.

## Guardrails to keep

- `import mo_sql_parsing` must stay under 0.2s — `tests/smoke_test1.py`. Currently ~16ms.
  See CLAUDE.md for what may and may not be imported at module scope.
