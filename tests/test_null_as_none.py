# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from unittest import TestCase

from mo_sql_parsing import parse

try:
    from tests.util import assertRaises
except ImportError:
    from .util import assertRaises  # RELATIVE IMPORT SO WE CAN RUN IN pyLibrary


class TestNull(TestCase):
    def test_default_null_value(self):
        result = parse("create table student (name varchar default null, sunny int primary key)", null=None,)
        expected = {"create table": {
            "name": "student",
            "columns": [
                {"name": "name", "type": {"varchar": {}}, "default": None},
                {"name": "sunny", "type": {"int": {}}, "primary_key": True},
            ],
        }}
        self.assertEqual(result, expected)

    def test_issue18(self):
        sql = "SELECT a, CASE WHEN some_columns = 'Bob' THEN NULL ELSE 'helloworld' END AS some_columns FROM mytable"
        result = parse(sql, null=None)
        expected = {
            "from": "mytable",
            "select": [
                {"value": "a"},
                {
                    "name": "some_columns",
                    "value": {"case": [
                        {"when": {"eq": ["some_columns", {"literal": "Bob"}]}, "then": None},
                        {"literal": "helloworld"},
                    ]},
                },
            ],
        }

        self.assertEqual(result, expected)

    def test_null_parameter2(self):
        sql = "select DECODE(NULL)"
        result = parse(sql, null=None)
        expected = {"select": {"value": {"decode": None}}}
        self.assertEqual(result, expected)

    def test_null_parameter3(self):
        sql = "select DECODE(NULL,a)"
        result = parse(sql, null=None)
        expected = {"select": {"value": {"decode": [None, "a"]}}}
        self.assertEqual(result, expected)

    def test_null_parameter4(self):
        sql = "select DECODE(a,NULL)"
        result = parse(sql, null=None)
        expected = {"select": {"value": {"decode": ["a", None]}}}
        self.assertEqual(result, expected)

    def test_null_value(self):
        sql = "select null"
        result = parse(sql, null=None)
        expected = {"select": {"value": None}}
        self.assertEqual(result, expected)

    def test_null_value2(self):
        sql = "select 'a',null"
        result = parse(sql, null=None)
        expected = {"select": [{"value": {"literal": "a"}}, {"value": None}]}
        self.assertEqual(result, expected)

    def test_null_value3(self):
        sql = "select null,b from x"
        result = parse(sql, null=None)
        expected = {"from": "x", "select": [{"value": None}, {"value": "b"}]}
        self.assertEqual(result, expected)

    def test_null_parameter(self):
        sql = "select DECODE(A, NULL, 'b')"
        result = parse(sql, null=None)
        expected = {"select": {"value": {"decode": ["A", None, {"literal": "b"}]}}}
        self.assertEqual(result, expected)
