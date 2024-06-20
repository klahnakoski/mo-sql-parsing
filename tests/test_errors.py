# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from unittest import skip

from mo_testing.fuzzytestcase import FuzzyTestCase, add_error_reporting

from mo_sql_parsing import parse, format, parse_mysql


@add_error_reporting
class TestErrors(FuzzyTestCase):
    def test_dash_in_tablename(self):
        #          012345678901234567890123456789012345678901234567890123456789
        try:
            parse_mysql("select * from coverage-summary.source.file.covered limit 20")
            self.assertTrue(False)
        except Exception as cause:
            self.assertIn("Use backticks (``) around identifiers", cause.message)

    def test_join_on_using_together(self):
        with self.assertRaises(["union", "order", "having", "limit", "where"]):
            parse("SELECT * FROM t1 JOIN t2 ON t1.id=t2.id USING (id)")

    def test_dash_in_tablename_general(self):
        with self.assertRaises(Exception):
            #      012345678901234567890123456789012345678901234567890123456789
            parse("select * from coverage-summary.source.file.covered limit 20")

    def test_join_on_using_together_general(self):
        with self.assertRaises(Exception):
            parse("SELECT * FROM t1 JOIN t2 ON t1.id=t2.id USING (id)")

    def test_bad_join_name(self):
        bad_json = {
            "select": {"value": "t1.field1"},
            "from": ["t1", {"left intro join": "t2", "on": {"eq": ["t1.id", "t2.id"]}}],
        }
        with self.assertRaises():
            format(bad_json)

    def test_order_by_must_follow_union(self):
        with self.assertRaises("UNION can not follow any of"):
            parse("select a from b order by a union select 2")

    def test_bad_order_by(self):
        with self.assertRaises("INTERSECT can not follow any of"):
            parse(
                """SELECT document_name FROM documents GROUP BY document_type_code ORDER BY COUNT(*) DESC LIMIT 3 INTERSECT SELECT document_name FROM documents GROUP BY document_structure_code ORDER BY COUNT(*) DESC LIMIT 3"""
            )

    def test_issue_50_subtraction3(self):
        sql = """select A from test-1nformation"""
        with self.assertRaises('found "-1nformati" (at char 18), (line:1, col:19)'):
            parse(sql)

    def test_issue_50_dashes_in_name(self):
        sql = """select col-cpu-usage from test-information"""
        with self.assertRaises("Use backticks (``) around identifiers"):
            parse_mysql(sql)

    def test_issue_50_subtraction1(self):
        sql = """select col-0pu-usage from test-information"""
        with self.assertRaises("Use backticks (``) around identifiers"):
            parse_mysql(sql)

    def test_issue_84_intersect(self):
        sql = """SELECT document_name FROM documents GROUP BY document_type_code ORDER BY count ( * ) DESC LIMIT 3 INTERSECT SELECT document_name FROM documents GROUP BY document_structure_code ORDER BY count ( * ) DESC LIMIT 3"""
        with self.assertRaises("INTERSECT can not follow any of"):
            parse(sql)

    @skip("TODO: this test is correct, please fix")
    def test_issue_88_parse_error(self):
        sql = """select c1, c as 't' from T"""
        with self.assertRaises("Expecting identifier, found \"'t'"):
            parse(sql)

    def test_issue_90_tablesample_error1(self):
        sql = "SELECT * FROM foo TABLESAMPLE(bernoulli) WHERE a < 42"
        with self.assertRaises('Expecting {bytes_constraint} | {bucket} | {int}, found "bernoulli'):
            parse(sql)

    def test_issue_90_tablesample_error2(self):
        sql = "SELECT * FROM foo f TABLESAMPLE(bernoulli) WHERE f.a < 42"
        with self.assertRaises('Expecting {bytes_constraint} | {bucket} | {int}, found "bernoulli'):
            parse(sql)

    def test_issue_143(self):
        sql = """WITH balance AS (
            SELECT * FROM `****`
        ), balance_settled_to_disregard AS (
            SELECT * FROM `***`
        ), tpv AS (
            SELECT
                IF(brand_description = 'VISA', 40,
                    IF(brand_description = 'MasterCard', 50,
        ...
        )"""
        with self.assertRaises('found "...\\n'):
            result = parse(sql)
