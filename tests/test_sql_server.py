# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from unittest import TestCase

from mo_sql_parsing import parse_sqlserver as parse


class TestSqlServer(TestCase):
    def test_select_top_5(self):
        sql = """
        select TOP (5)
            country_code,
            impact_code,
            impact_description,
            number_sites
        from EUNIS.v1.BISE_Country_Threats_Pressures_Number_Sites
        order by number_sites desc
        """
        result = parse(sql)

        self.assertEqual(
            result,
            {
                "top": 5,
                "select": [
                    {"value": "country_code"},
                    {"value": "impact_code"},
                    {"value": "impact_description"},
                    {"value": "number_sites"},
                ],
                "from": "EUNIS.v1.BISE_Country_Threats_Pressures_Number_Sites",
                "orderby": {"value": "number_sites", "sort": "desc"},
            },
        )

    def test_issue13_top(self):
        # https://docs.microsoft.com/en-us/sql/t-sql/queries/top-transact-sql?view=sql-server-ver15
        sql = "SELECT TOP 3 * FROM Customers"
        result = parse(sql)
        self.assertEqual(result, {"top": 3, "select": "*", "from": "Customers"})

        sql = "SELECT TOP func(value) WITH TIES *"
        result = parse(sql)
        self.assertEqual(
            result, {"top": {"value": {"func": "value"}, "ties": True}, "select": "*"},
        )

        sql = "SELECT TOP 1 PERCENT WITH TIES *"
        result = parse(sql)
        self.assertEqual(
            result, {"top": {"percent": 1, "ties": True}, "select": "*"},
        )

        sql = "SELECT TOP a(b) PERCENT item"
        result = parse(sql)
        self.assertEqual(
            result, {"top": {"percent": {"a": "b"}}, "select": {"value": "item"}},
        )

        sql = "SELECT TOP a(b) PERCENT"
        with self.assertRaises(Exception):
            parse(sql)  # MISSING ANY COLUMN

    def test_issue143a(self):
        sql = "Select [A] from dual"
        result = parse(sql)
        expected = {"select": {"value": "A"}, "from": "dual"}
        self.assertEqual(result, expected)

    def test_issue143b(self):
        sql = "Select [A] from [dual]"
        result = parse(sql)
        expected = {"select": {"value": "A"}, "from": "dual"}
        self.assertEqual(result, expected)

    def test_issue143c(self):
        sql = "Select [A] from dual [T1]"
        result = parse(sql)
        expected = {"select": {"value": "A"}, "from": {"value": "dual", "name": "T1"}}
        self.assertEqual(result, expected)

    def test_issue143d_quote(self):
        sql = 'Select ["]'
        result = parse(sql)
        expected = {"select": {"value": '"'}}
        self.assertEqual(result, expected)

    def test_issue143e_close(self):
        sql = "Select []]]"
        result = parse(sql)
        expected = {"select": {"value": "]"}}
        self.assertEqual(result, expected)

    def test_issue_52(self):
        sql = """SELECT [Timestamp] ,[RowsCount] ,[DataName] FROM [myDB].[myTable] where [Timestamp] >='2020-01-01' and [Timestamp]<'2020-12-31'"""
        result = parse(sql)
        expected = {
            "from": "myDB.myTable",
            "select": [{"value": "Timestamp"}, {"value": "RowsCount"}, {"value": "DataName"}],
            "where": {"and": [
                {"gte": ["Timestamp", {"literal": "2020-01-01"}]},
                {"lt": ["Timestamp", {"literal": "2020-12-31"}]},
            ]},
        }
        self.assertEqual(result, expected)

    def test_issue_78_top(self):
        sql = """
            SELECT TOP 1000 *
            FROM (
                    SELECT result
                    FROM dbo.b AS B
                ) AS X
            WHERE expected <> result
        """
        result = parse(sql)
        expected = {
            "from": {"name": "X", "value": {"from": {"name": "B", "value": "dbo.b"}, "select": {"value": "result"}}},
            "select": "*",
            "top": 1000,
            "where": {"neq": ["expected", "result"]},
        }
        self.assertEqual(result, expected)

    def test_issue_79a_no_lock(self):
        sql = """
        SELECT col1
        FROM table1 WITH (NOLOCK)
        """
        result = parse(sql)
        expected = {
            "from": {"value": "table1", "hint": "nolock"},
            "select": {"value": "col1"},
        }
        self.assertEqual(result, expected)

    def test_issue_79b_cross_apply(self):
        sql = """
        SELECT * FROM Department D 
        CROSS APPLY dbo.fn_GetAllEmployeeOfADepartment(D.DepartmentID)
        """
        result = parse(sql)
        expected = {
            "from": [
                {"name": "D", "value": "Department"},
                {"cross apply": {"dbo.fn_getallemployeeofadepartment": "D.DepartmentID"}},
            ],
            "select": "*",
        }
        self.assertEqual(result, expected)

    def test_issue_79b_outer_apply(self):
        sql = """
        SELECT * FROM Department D 
        OUTER APPLY dbo.fn_GetAllEmployeeOfADepartment(D.DepartmentID) 
        """
        result = parse(sql)
        expected = {
            "from": [
                {"name": "D", "value": "Department"},
                {"outer apply": {"dbo.fn_getallemployeeofadepartment": "D.DepartmentID"}},
            ],
            "select": "*",
        }
        self.assertEqual(result, expected)

    def test_issue_90_tablesample1(self):
        sql = "SELECT * FROM foo TABLESAMPLE bernoulli (1) WHERE a < 42"
        result = parse(sql)
        expected = {
            "from": {"tablesample": {"method": "bernoulli", "percent": 1}, "value": "foo"},
            "select": "*",
            "where": {"lt": ["a", 42]},
        }
        self.assertEqual(result, expected)

    def test_issue_90_tablesample2(self):
        sql = "SELECT * FROM foo f TABLESAMPLE bernoulli (1) WHERE f.a < 42"
        result = parse(sql)
        expected = {
            "from": {"name": "f", "tablesample": {"method": "bernoulli", "percent": 1}, "value": "foo"},
            "select": "*",
            "where": {"lt": ["f.a", 42]},
        }
        self.assertEqual(result, expected)

    def test_pivot_table(self):
        # FROM https://docs.microsoft.com/en-us/sql/t-sql/queries/from-using-pivot-and-unpivot?view=sql-server-ver16
        sql = """
        SELECT * FROM p  
        PIVOT  
        (  
        COUNT (id)  
        FOR E IN ( 250, 251, 256, 257, 260 )  
        ) AS pvt  
        """
        result = parse(sql)
        expected = {
            "select": "*",
            "from": [
                "p",
                {"pivot": {"name": "pvt", "aggregate": {"count": "id"}, "for": "E", "in": [250, 251, 256, 257, 260]}},
            ],
        }
        self.assertEqual(result, expected)

    def test_issue_157_describe(self):
        sql = """describe with_recommendations select * from temp"""
        result = parse(sql)
        expected = {
            "explain": {"from": "temp", "select": "*"},
            "with_recommendations": True,
        }
        self.assertEqual(result, expected)

    def test_try_cast_parsing(self):
        query = """SELECT TRY_CAST(a AS DECIMAL(10, 3)) FROM b.c"""
        result = parse(query)
        expected = {
            "select": {"value": {"try_cast": ["a", {"decimal": [10, 3]}]}},
            "from": "b.c",
        }
        self.assertEqual(result, expected)

    def test_issue_179_truncate1(self):
        sql = """TRUNCATE TABLE a.b"""
        result = parse(sql)
        expected = {"truncate": "a.b"}
        self.assertEqual(result, expected)

    def test_issue_179_truncate2(self):
        sql = """TRUNCATE TABLE a.b WITH (PARTITIONS (1,2,3))"""
        result = parse(sql)
        expected = {"truncate": "a.b", "partitions": [1, 2, 3]}
        self.assertEqual(result, expected)

    def test_issue_179_truncate3(self):
        sql = """TRUNCATE TABLE a.b WITH (PARTITIONS (1,2 to 9,4))"""
        result = parse(sql)
        expected = {"truncate": "a.b", "partitions": [1, {"range": [2, 9]}, 4]}
        self.assertEqual(result, expected)

    def test_issue_179_truncate3(self):
        sql = """TRUNCATE a.b WITH (PARTITIONS (1,2 to 9,4))"""
        result = parse(sql)
        expected = {"truncate": "a.b", "partitions": [1, {"range": [2, 9]}, 4]}
        self.assertEqual(result, expected)

    def test_issue_189_top(self):
        sql = """SELECT TOP 10 [Column] FROM A ORDER BY [relevance]"""
        result = parse(sql)
        expected = {"from": "A", "orderby": {"value": "relevance"}, "select": {"value": "Column"}, "top": 10}
        self.assertEqual(result, expected)

    def test_nliteral_parse(self):
        sql = """SELECT * FROM dbo.table WHERE a = N'Something'"""
        result = parse(sql)
        expected = {'select': '*', 'from': 'dbo.table', 'where': {'eq': ['a', {'nliteral': 'Something'}]}}
        self.assertEqual(result, expected)

    def test_issue_231(self):
        sql = """select count(*) as r_c, SUM(CASE WHEN NOT (t_dt = CAST(FORMAT(t_dt, 'yyyy-MM-ddTHH:mm:ss.ffffff') AS datetimeoffset)) THEN 1 ELSE 0 END) as e_c from [dbo].[table] """
        result = parse(sql)
        expected = {
            "select": [
                {"name": "r_c", "value": {"count": "*"}},
                {
                    "name": "e_c",
                    "value": {"sum": {
                        "case": [
                            {
                                "when": {"not": {"eq": [
                                    "t_dt",
                                    {"cast": [
                                        {"format": ["t_dt", {"literal": "yyyy-MM-ddTHH:mm:ss.ffffff"}]},
                                        {"datetimeoffset": {}},
                                    ]},
                                ]}},
                                "then": 1,
                            },
                            0,
                        ],
                    }},
                },
            ],
            "from": "dbo.table",
        }
        self.assertEqual(result, expected)

    def test_issue_237_declare_var(self):
        sql = """create procedure k() BEGIN
        DECLARE @MYVARIABLE INT = 42;
        END"""
        result = parse(sql)
        expected = {"create_procedure": {
            "name": "k",
            "body": {"block": {"declare": {"default": 42, "name": "@MYVARIABLE", "type": {"int": {}}, }}},
        }}
        self.assertEqual(result, expected)

    def test_issue_237_declare_var_with_as(self):
        sql = """create procedure k() BEGIN
        DECLARE @MYVARIABLE AS INT = 42;
        END"""
        result = parse(sql)
        expected = {"create_procedure": {
            "name": "k",
            "body": {"block": {"declare": {"default": 42, "name": "@MYVARIABLE", "type": {"int": {}}}}},
        }}
        self.assertEqual(result, expected)

    def test_issue_237_declare_multiple_vars(self):
        sql = """create procedure k() BEGIN
        DECLARE @MYVAR INT, @MYOTHERVAR DATE;
        END"""
        result = parse(sql)
        expected = {"create_procedure": {
            "name": "k",
            "body": {"block": {"declare": [
                {"name": "@MYVAR", "type": {"int": {}}},
                {"name": "@MYOTHERVAR", "type": {"date": {}}},
            ]}},
        }}
        self.assertEqual(result, expected)

    def test_issue_237_declare_multiple_vars_with_code(self):
        sql = """create procedure k() BEGIN
        DECLARE @MYVAR INT, @MYOTHERVAR DATE;
        SELECT a FROM rental;
        END"""
        result = parse(sql)
        expected = {"create_procedure": {
            "name": "k",
            "body": {"block": [
                {"declare": [{"name": "@MYVAR", "type": {"int": {}}}, {"name": "@MYOTHERVAR", "type": {"date": {}}}]},
                {"select": {"value": "a"}, "from": "rental"},
            ]},
        }}
        self.assertEqual(result, expected)
