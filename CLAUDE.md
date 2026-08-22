# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

The virtualenv is `.venv` (Windows: `.venv\Scripts\activate`, Linux: `source .venv/bin/activate`).

```bash
# install
python -m pip install --no-deps -r tests/requirements.lock
python -m pip install --upgrade -r packaging/requirements.txt

# whole suite (~1250 tests, ~20s)
python -m unittest discover .

# one file / class / test
python -m unittest tests.test_simple
python -m unittest tests.test_simple.TestSimple.test_two_tables

# import-cost smoke tests (also run in CI before the suite)
python tests/smoke_test1.py
python tests/smoke_test2.py

# upgrade test deps
pip-compile tests/requirements.txt -o tests/requirements.lock
```

To trace why a grammar rule does not match, wrap the parse in `with Debugger():`
(`from mo_parsing.debug import Debugger`) — see `tests/test_big_sql.py`.

## Import must stay cheap

`tests/smoke_test1.py` fails the build if `import mo_sql_parsing` exceeds **0.2 seconds**, and
`smoke_test2.py` fails if any `mo_imports` expectation is still outstanding after importing `format`.
`mo_sql_parsing/__init__.py` therefore imports only stdlib at module scope. Everything else —
`sql_parser`, `utils`, `formatting`, and `mo_dots` — is imported inside the function that needs it.
Adding a top-level `from mo_x import ...` to `__init__.py` will break the build; put it in the
function body instead.

Building a parser is also deferred: `_get_or_create_parser` constructs the grammar on first `parse()`
and memoizes it in `lookup_parsers` keyed by `(parser_name, all_columns)`.

## Architecture

Module dependency order (each imports only from those above it):

```
keywords.py   SQL tokens, RESERVED set, KNOWN_OPS, operator `precedence` table
utils.py      Call, scrub(), to_json_call, keyword/flag/assign grammar helpers
types.py      column type grammar (DECIMAL(2,3), ARRAY<...>, ...)
windows.py    OVER / PARTITION BY / frame grammar
sql_parser.py assembles all of the above into a ParserElement
formatting.py Formatter — the reverse direction, JSON -> SQL
```

`utils.py` also imports `simple_op` back from the package `__init__` — that is the one intentional cycle,
and it is why `__init__` must be importable without touching any submodule.

### Parse pipeline

1. `parse_delimiters()` splits the input on `;` (and honours `DELIMITER` statements for MySQL procedures).
2. `mo_parsing` matches each statement, producing `Call(op, args, kwargs)` objects from `utils.to_json_call`.
3. `scrub()` walks the result and calls `_utils.scrub_op` on each `Call` to emit the final JSON.

Step 3 is where the `calls=` option takes effect: `simple_op` emits `{op: args}`, `normal_op` emits
`{"op":…, "args":…, "kwargs":…}`.

### Global parse state

`_utils.scrub_op`, `_utils.fmap`, and `_utils.null_locations` are module-level globals set immediately
before each parse. A `parse_locker` `Lock` in `__init__.py` serializes calls so these globals are safe;
**one parse at a time, process-wide.** `null_locations` records where `SQL_NULL` landed so the `null=`
substitution can be applied as a post-pass.

### SQL flavours

`common_parser`, `mysql_parser`, `sqlserver_parser`, and `bigquery_parser` in `sql_parser.py` all call
the same `parser()` factory; they differ only in which string-literal and identifier grammars they pass:

| flavour    | string literals            | identifiers                                |
|------------|----------------------------|--------------------------------------------|
| common     | `'...'`                    | `"..."`, `` `...` ``                        |
| mysql      | `'...'`, `"..."`           | `` `...` ``, `[...]`, dashes warn          |
| sqlserver  | `'...'`                    | `"..."`, `` `...` ``, `[...]`, `@local`     |
| bigquery   | `'...'`, `"..."`           | `"..."`, `` `...` ``, dashes allowed        |

`[...]` is the flavour conflict that forces this split: SQLServer identifier vs. BigQuery array literal.

### Formatter

`Formatter.dispatch` routes on the JSON shape; a `_<op>` method (e.g. `_between`, `_trim`, `_case`)
overrides the generic `op()` handler for ops whose SQL is not `op(args)`. `isolate()` adds parentheses
using the shared `precedence` table from `keywords.py`, so parser and formatter agree on binding order.
The formatter lags the parser — not every parsed construct round-trips.

## Tests

Tests are plain `unittest.TestCase`, one file per dialect (`test_mysql.py`, `test_bigquery.py`, …) plus
dialect-neutral files (`test_simple.py`, `test_format_and_parse.py`, `test_formatting.py`). A test that
holds for all dialects belongs in the neutral files; put it in a dialect file only when the behaviour is
genuinely dialect-specific. The usual shape is `parse(sql)` compared against an expected dict with
`assertEqual`; `tests/util.py:assertRaises` checks error text.

`tests/test_working.py` is gitignored scratch space for the failing case you are currently chasing.

## Packaging

`packaging/setup.py` is generated from `packaging/setuptools.json` and the README; it is gitignored at the
repo root, and CI copies it there (`cp packaging/setup.py .`) before `pip install .`. Edit
`setuptools.json`, not a root `setup.py`. CI tests Python 3.8 through 3.14 and only runs on `master`
(pushes to `dev` skip the test job).
