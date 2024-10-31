# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from unittest import TestCase

from mo_testing.fuzzytestcase import add_error_reporting

from mo_sql_parsing import parse


@add_error_reporting
class TestOracle(TestCase):
    def test_issue_90_tablesample1(self):
        sql = "SELECT * FROM foo SAMPLE bernoulli (1) WHERE a < 42"
        result = parse(sql)
        expected = {
            "from": {"tablesample": {"method": "bernoulli", "percent": 1}, "value": "foo"},
            "select": {"all_columns": {}},
            "where": {"lt": ["a", 42]},
        }
        self.assertEqual(result, expected)

    def test_issue_90_tablesample2(self):
        sql = "SELECT * FROM foo SAMPLE(1) WHERE a < 42"
        result = parse(sql)
        expected = {
            "from": {"tablesample": {"percent": 1}, "value": "foo"},
            "select": {"all_columns": {}},
            "where": {"lt": ["a", 42]},
        }
        self.assertEqual(result, expected)

    def test_issue_157_describe(self):
        sql = """describe into s.t@database for select * from temp"""
        result = parse(sql)
        expected = {"explain": {"from": "temp", "select": {"all_columns": {}}}, "into": "s.t@database"}
        self.assertEqual(result, expected)

    def test_issue_157_describe2(self):
        sql = """explain plan into s.t@database for select * from temp"""
        result = parse(sql)
        expected = {"explain": {"from": "temp", "select": {"all_columns": {}}}, "into": "s.t@database"}
        self.assertEqual(result, expected)

    def test_natural_join(self):
        sql = """select * from A natural join b"""
        result = parse(sql)
        expected = {"select": {"all_columns": {}}, "from": ["A", {"natural join": "b"}]}
        self.assertEqual(result, expected)

    def test_validate_conversion_parsing(self):
        query = """SELECT VALIDATE_CONVERSION(a AS DECIMAL(10, 3)) FROM b.c"""
        result = parse(query)
        expected = {
            "select": {"value": {"validate_conversion": ["a", {"decimal": [10, 3]}]}},
            "from": "b.c",
        }
        self.assertEqual(result, expected)

    def test_issue_220(self):
        sql = """SELECT TO_TIMESTAMP(A DEFAULT NULL ON CONVERSION ERROR, 'DD/MM/YYYY HH24:MI:SS') FROM B.C"""
        result = parse(sql)
        expected = {
            "from": "B.C",
            "select": {"value": {
                "on_conversion_error": {"null": {}},
                "to_timestamp": ["A", {"literal": "DD/MM/YYYY HH24:MI:SS"}],
            }},
        }
        self.assertEqual(result, expected)
