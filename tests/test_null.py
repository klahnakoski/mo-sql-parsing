# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
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

    maxDiff = 50000

    def test_null_literal(self):
        sql = "select 'null'"
        result = parse(sql)
        expected = {"select": {"value": {"literal": "null"}}}
        self.assertEqual(result, expected)

    def test_null_value(self):
        sql = "select null"
        result = parse(sql)
        expected = {"select": {"value": {"null": {}}}}
        self.assertEqual(result, expected)

    def test_null_value2(self):
        sql = "select 'a',null"
        result = parse(sql)
        expected = {"select": [{"value": {"literal": "a"}}, {"value": {"null": {}}}]}
        self.assertEqual(result, expected)

    def test_value2(self):
        sql = "select 'a'"
        result = parse(sql)
        expected = {"select": {"value": {"literal": "a"}}}
        self.assertEqual(result, expected)

    def test_null_value3(self):
        sql = "select null,b from x"
        result = parse(sql)
        expected = {"from": "x", "select": [{"value": {"null": {}}}, {"value": "b"}]}
        self.assertEqual(result, expected)

    def test_null_parameter(self):
        sql = "select DECODE()"
        result = parse(sql)
        #  see to_json_call. when param is null, set {}.
        expected = {"select": {"value": {"decode": {}}}}
        # expected = {"select": {"value": {"decode": Null}}}
        self.assertEqual(result, expected)

    def test_null_parameter2(self):
        sql = "select DECODE(NULL)"
        result = parse(sql)
        expected = {"select": {"value": {"decode": {"null": {}}}}}
        # expected = {"select": {"value": {"decode": Null}}}
        self.assertEqual(result, expected)

    def test_null_parameter3(self):
        sql = "select DECODE(NULL,a)"
        result = parse(sql)
        expected = {"select": {"value": {"decode": [{"null": {}}, "a"]}}}
        self.assertEqual(result, expected)

    def test_null_parameter4(self):
        sql = "select DECODE(a,NULL)"
        result = parse(sql)
        expected = {"select": {"value": {"decode": ["a", {"null": {}}]}}}
        self.assertEqual(result, expected)

    def test_issue18(self):
        sql = (
            """SELECT a, CASE WHEN some_columns = 'Bob' THEN NULL ELSE 'helloworld' END AS some_columns FROM mytable"""
        )
        result = parse(sql)
        expected = {
            "from": "mytable",
            "select": [
                {"value": "a"},
                {
                    "name": "some_columns",
                    "value": {"case": [
                        {"when": {"eq": ["some_columns", {"literal": "Bob"}]}, "then": {"null": {}}},
                        {"literal": "helloworld"},
                    ]},
                },
            ],
        }

        self.assertEqual(result, expected)

    def test_issue_18(self):
        result = parse(
            """SELECT a, CASE WHEN some_columns = 'Bob' THEN NULL ELSE 'helloworld' END AS some_columns FROM mytable"""
        )
        expected = {
            "from": "mytable",
            "select": [
                {"value": "a"},
                {
                    "name": "some_columns",
                    "value": {"case": [
                        {"then": {"null": {}}, "when": {"eq": ["some_columns", {"literal": "Bob"}]}},
                        {"literal": "helloworld"},
                    ]},
                },
            ],
        }
        self.assertEqual(result, expected)
