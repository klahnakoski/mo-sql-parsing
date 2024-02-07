# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Original Author: https://github.com/ilyakochik
# Original Code: https://github.com/klahnakoski/mo-sql-parsing/issues/228#issuecomment-1932588289


from __future__ import annotations
import mo_sql_parsing
import mo_parsing.utils
from mo_future import text, number_types, binary_type
from mo_parsing import *
from mo_sql_parsing.utils import scrub_op, SQL_NULL, Call
from collections.abc import Generator


class SqlTree:
    start: int = None
    end: int = None

    @staticmethod
    def get_meta_keys() -> tuple[str, str]:
        return ("start", "end")

    def set_meta(self, **kwargs) -> SqlTree:
        for k in kwargs:
            assert k in SqlTree.get_meta_keys()
            setattr(self, k, kwargs[k])
        return self

    def get_meta(self) -> dict[str, object]:
        return {k: getattr(self, k, None) for k in SqlTree.get_meta_keys()}

    def copy_meta(self, other: SqlTree) -> SqlTree:
        return self.set_meta(**other.get_meta())


class SqlList(list, SqlTree):
    def items(self) -> Generator[tuple[int, object]]:
        return enumerate(self)


class SqlDict(dict, SqlTree):
    pass


class SqlValue(SqlTree):
    value: str | int = None

    def __init__(self, value: str | int):
        self.value = value

    def __str__(self) -> str:
        return self.value.__str__()

    def __repr__(self) -> str:
        return self.value.__repr__()

    def items(self) -> Generator[tuple[int, str | int]]:
        return enumerate([self.value])


flat_keys = "name", "value", "all_columns"
transpile_map = {list: SqlList, dict: SqlDict, int: SqlValue, str: SqlValue}


# Results of original `scrub` function is appended to a list, so apply it after `_parse`
mo_sql_parsing.utils.scrub = lambda x: x


def parse(sql: str) -> SqlTree:
    parsed = mo_sql_parsing.parse(sql)
    tree = _transpile(parsed)
    tree = _squash(tree)
    _fix(tree)
    _check(tree, sql)
    return tree


def _check(tree: SqlTree, sql: str) -> None:
    meta = tree.get_meta()
    if all(v is not None for v in meta.values()):
        print(str(tree)[0:20], " === ", sql[meta["start"] : meta["end"]])

    if isinstance(tree, (SqlDict, SqlList)):
        for k, v in tree.items():
            _check(v, sql)


def _fix(tree: SqlTree) -> None:
    # TODO: fix parser to always have start and end without these hacks
    if isinstance(tree, SqlList):
        start = (r.start for r in tree if r.start is not None)
        end = (r.end for r in tree if r.end is not None)
        tree.set_meta(start=min(start, default=None), end=max(end, default=None))
    elif isinstance(tree, SqlDict) and len(tree) == 1:
        child = list(tree.keys()).pop()
        if not all(v is not None for v in tree[child].get_meta().values()):
            tree[child].copy_meta(tree)

    if isinstance(tree, SqlTree):
        for k, v in tree.items():
            _fix(v)


def _squash(dirty: SqlTree, parent=None) -> SqlTree:
    global flat_keys

    # Recursively clean up the tree
    if isinstance(dirty, SqlList):
        clean = [_squash(r, dirty) for r in dirty]
        clean = [r for r in clean if r is not None]
        if len(clean) > 1:
            clean = SqlList(clean)
        elif len(clean) == 1 and clean[0] is not None:
            clean = clean[0]
        else:
            clean = None
    elif isinstance(dirty, SqlDict):
        clean = {k: _squash(v, dirty) for k, v in dirty.items()}
        clean = {
            k: v if isinstance(v, list) or k in flat_keys else SqlList([v]).copy_meta(v)
            for k, v in clean.items()
            if v is not None
        }
        clean = SqlDict(clean)
    elif dirty is None or isinstance(dirty, SqlValue):
        clean = dirty
    else:
        raise NotImplementedError(f"Not implemented for {dirty.__class__}")

    # Preserve meta attributes
    if clean is None:
        return clean
    elif all(v is not None for v in clean.get_meta().values()):
        return clean
    elif all(v is not None for v in dirty.get_meta().values()):
        return clean.copy_meta(dirty)
    elif all(v is not None for v in parent.get_meta().values()):
        return clean.copy_meta(parent)
    else:
        return clean


def _transpile(dirty: object) -> SqlTree:
    global transpile_map
    loc_attrs, loc = ("start", "end"), {}
    clean = None

    # Parse depending on type
    if dirty is SQL_NULL or dirty is None:
        clean = None
    elif isinstance(dirty, (text, number_types)):
        # TODO: Simple tokens do not have `start` and `end`
        clean = dirty
    elif isinstance(dirty, binary_type):
        clean = dirty.decode("utf8")
    elif isinstance(dirty, list):
        clean = [_transpile(r) for r in dirty]
    elif isinstance(dirty, dict):
        clean = {k: _transpile(v) for k, v in dirty.items()}
    elif isinstance(dirty, Call):
        kwargs = _transpile(dirty.kwargs)
        args = _transpile(dirty.args)
        clean = scrub_op(dirty.op, args, kwargs)
        # TODO: Call object has no `start` and `end`
    elif isinstance(dirty, mo_parsing.results.ForwardResults):
        loc = {a: getattr(dirty, a, None) for a in loc_attrs}
        clean = _transpile(dirty.tokens)
    elif isinstance(dirty, mo_parsing.results.ParseResults):
        loc = {a: getattr(dirty, a, None) for a in loc_attrs}
        tokens = dict(dirty.items()) or dirty.tokens
        clean = _transpile(tokens)
        # TODO: "*" is {all_columns: {}}, while "tbl.*" is {all_columns: "tbl"}
        #       for consistency better {all_columns: ''}
        # TODO: ParseResults often has `start=-1` and `end=0`
    else:
        raise NotImplementedError(f"Not implemented for {dirty.__class__}")

    # Transpile to Sql classes
    if clean.__class__ in transpile_map:
        clean = transpile_map[clean.__class__](clean)

    # Update meta attributes if captured
    if loc and all(loc[v] is not None and loc[v] >= 0 for v in loc_attrs):
        clean.set_meta(**loc)

    return clean