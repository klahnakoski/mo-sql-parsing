from unittest import TestCase

from mo_logs import logger
from mo_testing.fuzzytestcase import add_error_reporting

from mo_sql_parsing import parse as _parse, format
from tests.test_format_and_parse import EXCEPTION_MESSAGE


def parse(sql):
    return _parse(sql, all_columns="*")


@add_error_reporting
class TestV9(TestCase):
    def verify_formatting(self, expected_sql, expected_json):
        new_sql = ""
        new_json = ""
        try:
            new_sql = format(expected_json)
            new_json = parse(new_sql)
            self.assertEqual(new_json, expected_json)
        except Exception as cause:
            logger.error(
                EXCEPTION_MESSAGE,
                expected_sql=expected_sql,
                expected_json=expected_json,
                new_sql=new_sql,
                new_json=new_json,
                cause=cause,
            )

    def test_008(self):
        expected_sql = "SELECT *, * FROM test1"
        expected_json = {"from": "test1", "select": ["*", "*"]}
        self.verify_formatting(expected_sql, expected_json)

    def test_009(self):
        expected_sql = "SELECT *, min(f1,f2), max(f1,f2) FROM test1"
        expected_json = {
            "from": "test1",
            "select": ["*", {"value": {"min": ["f1", "f2"]}}, {"value": {"max": ["f1", "f2"]}}],
        }
        self.verify_formatting(expected_sql, expected_json)

    def test_014(self):
        expected_sql = "SELECT *, 'hi' FROM test1, test2"
        expected_json = {
            "from": ["test1", "test2"],
            "select": ["*", {"value": {"literal": "hi"}}],
        }
        self.verify_formatting(expected_sql, expected_json)

    def test_issue_99_select_except(self):
        result = parse("SELECT * EXCEPT(x) FROM `a.b.c`")
        expected = {"from": "a..b..c", "select_except": {"value": "x"}}
        self.assertEqual(result, expected)

    def test_issue_206(self):
        query = """
           with raw_data as (
              select 
                     * 
              from UNNEST(GENERATE_ARRAY(1, 2)) as col1,
              UNNEST(GENERATE_ARRAY(10, 12)) as col2,
              UNNEST(GENERATE_ARRAY(20, 22)) as col3
           )
           select 
               * except(col3), 
               col3 + col1 as new_col
           from raw_data
           """
        result = parse(query)
        expected = {
            "from": "raw_data",
            "select": {"name": "new_col", "value": {"add": ["col3", "col1"]}},
            "select_except": {"value": "col3"},
            "with": {
                "name": "raw_data",
                "value": {
                    "from": [
                        {"name": "col1", "value": {"unnest": {"generate_array": [1, 2]}}},
                        {"name": "col2", "value": {"unnest": {"generate_array": [10, 12]}}},
                        {"name": "col3", "value": {"unnest": {"generate_array": [20, 22]}}},
                    ],
                    "select": "*",
                },
            },
        }

        self.assertEqual(result, expected)
