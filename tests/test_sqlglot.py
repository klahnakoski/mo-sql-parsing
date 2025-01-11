# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#

# THE SQL FOR THESE TESTS WERE SNAGGED FROM
# https://github.com/tobymao/sqlglot/blob/15fbef02d56d87036d7cace0b7333dd2b341445e/tests/fixtures/identity.sql
# UNDER THE MIT LICENSE DURING NOV 2021


from unittest import skip, TestCase

from mo_sql_parsing import parse


class TestSqlGlot(TestCase):
    def test_issue_46_sqlglot_0(self):
        sql = """SET x = 1"""
        result = parse(sql)
        expected = {"set": {"x": 1}}
        self.assertEqual(result, expected)

    @skip("set requires =")
    def test_issue_46_sqlglot_1(self):
        sql = """SET -v"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    @skip("does not pass yet")
    def test_issue_46_sqlglot_2(self):
        sql = """ADD JAR s3://bucket"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    @skip("does not pass yet")
    def test_issue_46_sqlglot_3(self):
        sql = """ADD JARS s3://bucket, c"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    @skip("does not pass yet")
    def test_issue_46_sqlglot_4(self):
        sql = """ADD FILE s3://file"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    @skip("does not pass yet")
    def test_issue_46_sqlglot_5(self):
        sql = """ADD FILES s3://file, s3://a"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    @skip("does not pass yet")
    def test_issue_46_sqlglot_6(self):
        sql = """ADD ARCHIVE s3://file"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    @skip("does not pass yet")
    def test_issue_46_sqlglot_7(self):
        sql = """ADD ARCHIVES s3://file, s3://a"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_8(self):
        sql = """SELECT TRANSFORM(a, (b) -> b) AS x"""
        result = parse(sql)
        expected = {"select": {"name": "x", "value": {"transform": ["a", {"lambda": "b", "params": "b"}]}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_9(self):
        sql = """SELECT AGGREGATE(a, (a, b) -> a + b) AS x"""
        result = parse(sql)
        expected = {"select": {
            "name": "x",
            "value": {"aggregate": ["a", {"lambda": {"add": ["a", "b"]}, "params": ["a", "b"]}]},
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_10(self):
        sql = """SELECT X((a, b) -> a + b, (z) -> z) AS x"""
        result = parse(sql)
        expected = {"select": {
            "name": "x",
            "value": {"x": [{"lambda": {"add": ["a", "b"]}, "params": ["a", "b"]}, {"lambda": "z", "params": "z"}]},
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_11(self):
        sql = """SELECT X((a) -> "a" + ("z" - 1))"""
        result = parse(sql)
        expected = {"select": {"value": {"x": {"lambda": {"add": ["a", {"sub": ["z", 1]}]}, "params": "a"}}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_12(self):
        sql = """SELECT EXISTS(ARRAY(2, 3), (x) -> x % 2 = 0)"""
        result = parse(sql)
        expected = {"select": {"value": {"exists": [
            {"create_array": [2, 3]},
            {"lambda": {"eq": [{"mod": ["x", 2]}, 0]}, "params": "x"},
        ]}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_13(self):
        sql = """SELECT CASE TEST(1) + x[0] WHEN 1 THEN 1 ELSE 2 END"""
        result = parse(sql)
        expected = {"select": {"value": {"case": [
            {"then": 1, "when": {"eq": [{"add": [{"test": 1}, {"get": ["x", 0]}]}, 1]}},
            2,
        ]}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_14(self):
        sql = """SELECT CASE x[0] WHEN 1 THEN 1 ELSE 2 END"""
        result = parse(sql)
        expected = {"select": {"value": {"case": [{"then": 1, "when": {"eq": [{"get": ["x", 0]}, 1]}}, 2]}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_15(self):
        sql = """SELECT a FROM test TABLESAMPLE(BUCKET 1 OUT OF 5)"""
        result = parse(sql)
        expected = {
            "from": {"tablesample": {"bucket": [1, 5]}, "value": "test"},
            "select": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_16(self):
        sql = """SELECT a FROM test TABLESAMPLE(BUCKET 1 OUT OF 5 ON x)"""
        result = parse(sql)
        expected = {
            "from": {"tablesample": {"bucket": [1, 5], "on": "x"}, "value": "test"},
            "select": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_17(self):
        sql = """SELECT a FROM test TABLESAMPLE(BUCKET 1 OUT OF 5 ON RAND())"""
        result = parse(sql)
        expected = {
            "from": {"tablesample": {"bucket": [1, 5], "on": {"rand": {}}}, "value": "test"},
            "select": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_18(self):
        sql = """SELECT a FROM test TABLESAMPLE(0.1 PERCENT)"""
        result = parse(sql)
        expected = {
            "from": {"tablesample": {"percent": 0.1}, "value": "test"},
            "select": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_19(self):
        sql = """SELECT a FROM test TABLESAMPLE(100 ROWS)"""
        result = parse(sql)
        expected = {
            "from": {"tablesample": {"rows": 100}, "value": "test"},
            "select": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_19b(self):
        sql = """SELECT a FROM test TABLESAMPLE(100G)"""
        result = parse(sql)
        expected = {
            "from": {"tablesample": {"bytes": 100_000_000_000}, "value": "test"},
            "select": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_20(self):
        sql = """SELECT CAST(a AS DECIMAL(1)) FROM test"""
        result = parse(sql)
        expected = {
            "from": "test",
            "select": {"value": {"cast": ["a", {"decimal": 1}]}},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_21(self):
        sql = """SELECT CAST(a AS MAP(INT, INT)) FROM test"""
        result = parse(sql)
        expected = {
            "from": "test",
            "select": {"value": {"cast": ["a", {"map": [{"int": {}}, {"int": {}}]}]}},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_22(self):
        sql = """SELECT CAST(a AS ARRAY(INT)) FROM test"""
        result = parse(sql)
        expected = {
            "from": "test",
            "select": {"value": {"cast": ["a", {"array": {"int": {}}}]}},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_23(self):
        sql = """SELECT 1 FROM a LEFT INNER JOIN b ON a.foo = b.bar"""
        result = parse(sql)
        expected = {
            "from": ["a", {"on": {"eq": ["a.foo", "b.bar"]}, "left inner join": "b"}],
            "select": {"value": 1},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_24(self):
        sql = """SELECT 1 FROM a OUTER JOIN b ON a.foo = b.bar"""
        result = parse(sql)
        expected = {
            "from": ["a", {"on": {"eq": ["a.foo", "b.bar"]}, "outer join": "b"}],
            "select": {"value": 1},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_25(self):
        sql = """SELECT 1 EXCEPT DISTINCT SELECT 2"""
        result = parse(sql)
        expected = {"except_distinct": [{"select": {"value": 1}}, {"select": {"value": 2}}]}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_26(self):
        sql = """SELECT 1 INTERSECT DISTINCT SELECT 2"""
        result = parse(sql)
        expected = {"intersect_distinct": [{"select": {"value": 1}}, {"select": {"value": 2}}]}
        self.assertEqual(result, expected)

    @skip("alias (AS x) in compound operator not allowed https://sqlite.org/syntax/select-stmt.html")
    def test_issue_46_sqlglot_27(self):
        sql = """SELECT * FROM ((SELECT 1) AS a UNION ALL (SELECT 2) AS b)"""
        result = parse(sql)
        expected = {
            "select": "*",
            "from": {"union_all": [
                {"from": {"value": {"select": 1}, "name": "a"}},
                {"from": {"value": {"select": 2}, "name": "b"}},
            ]},
        }
        self.assertEqual(result, expected)

    @skip("JOIN is not a compound operator https://sqlite.org/syntax/select-stmt.html")
    def test_issue_46_sqlglot_28(self):
        sql = """SELECT 1 FROM ((SELECT 1) AS a JOIN (SELECT 1) AS b)"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_29(self):
        sql = """VALUES (1) UNION SELECT * FROM x"""
        result = parse(sql)
        expected = {"union": [{"select": {"value": 1}}, {"from": "x", "select": "*"}]}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_30(self):
        sql = (
            """WITH RECURSIVE T(n) AS (VALUES (1) UNION ALL SELECT n + 1 FROM t WHERE n < 100) SELECT SUM(n) FROM t"""
        )
        result = parse(sql)
        expected = {
            "from": "t",
            "select": {"value": {"sum": "n"}},
            "with_recursive": {
                "name": {"T": "n"},
                "value": {"union_all": [
                    {"select": {"value": 1}},
                    {"from": "t", "select": {"value": {"add": ["n", 1]}}, "where": {"lt": ["n", 100]}},
                ]},
            },
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_31(self):
        sql = """WITH RECURSIVE T(n, m) AS (VALUES (1, 2) UNION ALL SELECT n + 1, n + 2 FROM t) SELECT SUM(n) FROM t"""
        result = parse(sql)
        expected = {
            "from": "t",
            "select": {"value": {"sum": "n"}},
            "with_recursive": {
                "name": {"T": ["n", "m"]},
                "value": {"union_all": [
                    {"select": [{"value": 1}, {"value": 2}]},
                    {"from": "t", "select": [{"value": {"add": ["n", 1]}}, {"value": {"add": ["n", 2]}}]},
                ]},
            },
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_32(self):
        sql = """SELECT * FROM (WITH y AS (SELECT 1 AS z) SELECT z FROM y) AS x"""
        result = parse(sql)
        expected = {
            "from": {
                "name": "x",
                "value": {
                    "from": "y",
                    "select": {"value": "z"},
                    "with": {"name": "y", "value": {"select": {"name": "z", "value": 1}}},
                },
            },
            "select": "*",
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_33(self):
        sql = """SELECT SUM(x) OVER(PARTITION BY a ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)"""
        result = parse(sql)
        expected = {"select": {"over": {"partitionby": "a", "range": {"max": 0}}, "value": {"sum": "x"}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_34(self):
        sql = """SELECT SUM(x) OVER(PARTITION BY a ORDER BY b RANGE BETWEEN INTERVAL '1' DAY PRECEDING AND CURRENT ROW)"""
        result = parse(sql)
        expected = {"select": {
            "over": {
                "orderby": {"value": "b"},
                "partitionby": "a",
                "range": {"max": 0, "min": {"neg": {"interval": [1, "day"]}}},
            },
            "value": {"sum": "x"},
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_35(self):
        sql = """SELECT SUM(x) OVER(PARTITION BY a ORDER BY b RANGE BETWEEN INTERVAL '1' DAY PRECEDING AND INTERVAL '2' DAYS FOLLOWING)"""
        result = parse(sql)
        expected = {"select": {
            "over": {
                "orderby": {"value": "b"},
                "partitionby": "a",
                "range": {"max": {"neg": {"interval": [2, "day"]}}, "min": {"neg": {"interval": [1, "day"]}}},
            },
            "value": {"sum": "x"},
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_36(self):
        sql = """SELECT SUM(x) OVER(PARTITION BY a ORDER BY b RANGE BETWEEN INTERVAL '1' DAY PRECEDING AND UNBOUNDED FOLLOWING)"""
        result = parse(sql)
        expected = {"select": {
            "over": {
                "orderby": {"value": "b"},
                "partitionby": "a",
                "range": {"min": {"neg": {"interval": [1, "day"]}}},
            },
            "value": {"sum": "x"},
        }}
        self.assertEqual(result, expected)

    @skip("PRECEDING must have a qualifier https://www.sqlite.org/windowfunctions.html")
    def test_issue_46_sqlglot_37(self):
        sql = """SELECT SUM(x) OVER(PARTITION BY a ROWS BETWEEN UNBOUNDED PRECEDING AND PRECEDING)"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_38(self):
        sql = """SELECT SUM(x) OVER(PARTITION BY a ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)"""
        result = parse(sql)
        expected = {"select": {"over": {"partitionby": "a", "range": {}}, "value": {"sum": "x"}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_39(self):
        sql = """SELECT SUM(x) OVER(PARTITION BY a ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING)"""
        result = parse(sql)
        expected = {"select": {"over": {"partitionby": "a", "range": {"min": 0}}, "value": {"sum": "x"}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_40(self):
        sql = """SELECT SUM(x) OVER(PARTITION BY a RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)"""
        result = parse(sql)
        expected = {"select": {"over": {"partitionby": "a", "range": {"max": 0}}, "value": {"sum": "x"}}}
        self.assertEqual(result, expected)

    @skip("values must be qualified with preceding/following https://www.sqlite.org/windowfunctions.html")
    def test_issue_46_sqlglot_41(self):
        sql = """SELECT SUM(x) OVER(PARTITION BY a RANGE BETWEEN 1 AND 3)"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    @skip("values must be qualified with preceding/following https://www.sqlite.org/windowfunctions.html")
    def test_issue_46_sqlglot_42(self):
        sql = """SELECT SUM(x) OVER(PARTITION BY a RANGE BETWEEN 1 FOLLOWING AND 3)"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_43(self):
        sql = """SELECT SUM(x) OVER(PARTITION BY a RANGE BETWEEN 1 FOLLOWING AND UNBOUNDED FOLLOWING)"""
        result = parse(sql)
        expected = {"select": {"over": {"partitionby": "a", "range": {"min": 1}}, "value": {"sum": "x"}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_44(self):
        sql = """SELECT ARRAY(ARRAY(0))[0][0] FROM x"""
        result = parse(sql)
        expected = {
            "from": "x",
            "select": {"value": {"get": [{"get": [{"create_array": {"create_array": 0}}, 0]}, 0]}},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_45(self):
        sql = """SELECT MAP[ARRAY('x'), ARRAY(0)]['x'] FROM x"""
        result = parse(sql)
        expected = {
            "from": "x",
            "select": {"value": {"get": [
                {"create_map": [{"create_array": {"literal": "x"}}, {"create_array": 0}]},
                {"literal": "x"},
            ]}},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_46(self):
        sql = """SELECT student, score FROM tests LATERAL VIEW EXPLODE(scores) t AS score"""
        result = parse(sql)
        expected = {
            "from": ["tests", {"lateral view": {"name": {"t": "score"}, "value": {"explode": "scores"}}}],
            "select": [{"value": "student"}, {"value": "score"}],
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_47(self):
        sql = """SELECT student, score FROM tests LATERAL VIEW EXPLODE(scores) t AS score, name"""
        result = parse(sql)
        expected = {
            "from": ["tests", {"lateral view": {"name": {"t": ["score", "name"]}, "value": {"explode": "scores"}}}],
            "select": [{"value": "student"}, {"value": "score"}],
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_48(self):
        sql = """SELECT student, score FROM tests LATERAL VIEW OUTER EXPLODE(scores) t AS score, name"""
        result = parse(sql)
        expected = {
            "from": [
                "tests",
                {"lateral view outer": {"name": {"t": ["score", "name"]}, "value": {"explode": "scores"}}},
            ],
            "select": [{"value": "student"}, {"value": "score"}],
        }

        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_49(self):
        sql = """SELECT tf.* FROM (SELECT 0) AS t LATERAL VIEW STACK(1, 2) tf"""
        result = parse(sql)
        expected = {
            "from": [
                {"name": "t", "value": {"select": {"value": 0}}},
                {"lateral view": {"name": "tf", "value": {"stack": 2, "width": 1}}},
            ],
            "select": {"value": "tf.*"},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_50(self):
        sql = """SELECT tf.* FROM (SELECT 0) AS t LATERAL VIEW STACK(1, 2) tf AS col0, col1, col2"""
        result = parse(sql)
        expected = {
            "from": [
                {"name": "t", "value": {"select": {"value": 0}}},
                {"lateral view": {"name": {"tf": ["col0", "col1", "col2"]}, "value": {"stack": 2, "width": 1}}},
            ],
            "select": {"value": "tf.*"},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_51(self):
        sql = """SELECT student, score FROM tests CROSS JOIN UNNEST(scores) WITH ORDINALITY AS t (a, b)"""
        result = parse(sql)
        expected = {
            "from": [
                "tests",
                {"cross join": {"name": {"t": ["a", "b"]}, "value": {"unnest": "scores"}, "with_ordinality": True}},
            ],
            "select": [{"value": "student"}, {"value": "score"}],
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_52(self):
        sql = """CREATE TABLE a.b AS SELECT 1"""
        result = parse(sql)
        expected = {"create table": {"name": "a.b", "query": {"select": {"value": 1}}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_53(self):
        sql = """CREATE TABLE a.b AS SELECT a FROM a.c"""
        result = parse(sql)
        expected = {"create table": {"name": "a.b", "query": {"from": "a.c", "select": {"value": "a"}}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_54(self):
        sql = """CREATE TABLE IF NOT EXISTS x AS SELECT a FROM d"""
        result = parse(sql)
        expected = {"create table": {"name": "x", "query": {"from": "d", "select": {"value": "a"}}, "replace": False}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_55(self):
        sql = """CREATE TEMPORARY TABLE x AS SELECT a FROM d"""
        result = parse(sql)
        expected = {"create table": {
            "name": "x",
            "query": {"from": "d", "select": {"value": "a"}},
            "temporary": True,
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_56(self):
        sql = """CREATE TEMPORARY TABLE IF NOT EXISTS x AS SELECT a FROM d"""
        result = parse(sql)
        expected = {"create table": {
            "name": "x",
            "query": {"from": "d", "select": {"value": "a"}},
            "replace": False,
            "temporary": True,
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_57(self):
        sql = """CREATE VIEW x AS SELECT a FROM b"""
        result = parse(sql)
        expected = {"create view": {"name": "x", "query": {"from": "b", "select": {"value": "a"}}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_58(self):
        sql = """CREATE VIEW IF NOT EXISTS x AS SELECT a FROM b"""
        result = parse(sql)
        expected = {"create view": {"name": "x", "query": {"from": "b", "select": {"value": "a"}}, "replace": False}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_59(self):
        sql = """CREATE OR REPLACE VIEW x AS SELECT *"""
        result = parse(sql)
        expected = {"create view": {"name": "x", "query": {"select": "*"}, "replace": True}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_60(self):
        sql = """CREATE OR REPLACE TEMPORARY VIEW x AS SELECT *"""
        result = parse(sql)
        expected = {"create view": {"name": "x", "query": {"select": "*"}, "replace": True, "temporary": True}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_61(self):
        sql = """CREATE TEMPORARY VIEW x AS SELECT a FROM d"""
        result = parse(sql)
        expected = {"create view": {"name": "x", "query": {"from": "d", "select": {"value": "a"}}, "temporary": True}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_62(self):
        sql = """CREATE TEMPORARY VIEW IF NOT EXISTS x AS SELECT a FROM d"""
        result = parse(sql)
        expected = {"create view": {
            "name": "x",
            "query": {"from": "d", "select": {"value": "a"}},
            "replace": False,
            "temporary": True,
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_63(self):
        sql = """CREATE TEMPORARY VIEW x AS WITH y AS (SELECT 1) SELECT * FROM y"""
        result = parse(sql)
        expected = {"create view": {
            "name": "x",
            "query": {"from": "y", "select": "*", "with": {"name": "y", "value": {"select": {"value": 1}}}},
            "temporary": True,
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_64(self):
        sql = """CREATE TABLE z (a INT, b VARCHAR, c VARCHAR(100), d DECIMAL(5, 3))"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "a", "type": {"int": {}}},
                {"name": "b", "type": {"varchar": {}}},
                {"name": "c", "type": {"varchar": 100}},
                {"name": "d", "type": {"decimal": [5, 3]}},
            ],
            "name": "z",
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_65(self):
        sql = """CREATE TABLE z (a INT, b VARCHAR COMMENT 'z', c VARCHAR(100) COMMENT 'z', d DECIMAL(5, 3))"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "a", "type": {"int": {}}},
                {"comment": {"literal": "z"}, "name": "b", "type": {"varchar": {}}},
                {"comment": {"literal": "z"}, "name": "c", "type": {"varchar": 100}},
                {"name": "d", "type": {"decimal": [5, 3]}},
            ],
            "name": "z",
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_66(self):
        sql = """CREATE TABLE z (a INT(11) DEFAULT NULL COMMENT '客户id')"""
        result = parse(sql)
        expected = {"create table": {
            "columns": {"comment": {"literal": "客户id"}, "default": {"null": {}}, "name": "a", "type": {"int": 11}},
            "name": "z",
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_67(self):
        sql = """CREATE TABLE z (a INT(11) NOT NULL DEFAULT 1)"""
        result = parse(sql)
        expected = {"create table": {
            "columns": {"default": 1, "name": "a", "nullable": False, "type": {"int": 11}},
            "name": "z",
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_68(self):
        sql = """CREATE TABLE z (a INT(11) NOT NULL COLLATE utf8_bin AUTO_INCREMENT)"""
        result = parse(sql)
        expected = {"create table": {
            "columns": {
                "auto_increment": True,
                "collate": "utf8_bin",
                "name": "a",
                "nullable": False,
                "type": {"int": 11},
            },
            "name": "z",
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_69(self):
        sql = """CREATE TABLE z (a INT, PRIMARY KEY(a))"""
        result = parse(sql)
        expected = {"create table": {
            "columns": {"name": "a", "type": {"int": {}}},
            "constraint": {"primary_key": {"columns": "a"}},
            "name": "z",
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_70(self):
        sql = """CREATE TABLE z (a INT) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARACTER SET=utf8 COLLATE=utf8_bin COMMENT='x'"""
        result = parse(sql)
        expected = {"create table": {
            "auto_increment": 1,
            "collate": "utf8_bin",
            "columns": {"name": "a", "type": {"int": {}}},
            "comment": {"literal": "x"},
            "default_character_set": "utf8",
            "engine": "InnoDB",
            "name": "z",
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_71(self):
        sql = """CREATE TABLE z (a INT DEFAULT NULL, PRIMARY KEY(a)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARACTER SET=utf8 COLLATE=utf8_bin COMMENT='x'"""
        result = parse(sql)
        expected = {"create table": {
            "auto_increment": 1,
            "collate": "utf8_bin",
            "columns": {"default": {"null": {}}, "name": "a", "type": {"int": {}}},
            "comment": {"literal": "x"},
            "constraint": {"primary_key": {"columns": "a"}},
            "default_character_set": "utf8",
            "engine": "InnoDB",
            "name": "z",
        }}

        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_72(self):
        sql = """CACHE TABLE x"""
        result = parse(sql)
        expected = {"cache": {"name": "x"}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_73(self):
        sql = """CACHE LAZY TABLE x"""
        result = parse(sql)
        expected = {"cache": {"lazy": True, "name": "x"}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_74(self):
        sql = """CACHE LAZY TABLE x OPTIONS('storageLevel' = value)"""
        result = parse(sql)
        expected = {"cache": {"lazy": True, "name": "x", "options": {"storageLevel": "value"}}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_75(self):
        sql = """CACHE LAZY TABLE x OPTIONS('storageLevel' = value) AS SELECT 1"""
        result = parse(sql)
        expected = {"cache": {
            "lazy": True,
            "name": "x",
            "options": {"storageLevel": "value"},
            "query": {"select": {"value": 1}},
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_76(self):
        sql = """CACHE LAZY TABLE x OPTIONS('storageLevel' = value) AS WITH a AS (SELECT 1) SELECT a.* FROM a"""
        result = parse(sql)
        expected = {"cache": {
            "lazy": True,
            "name": "x",
            "options": {"storageLevel": "value"},
            "query": {
                "from": "a",
                "select": {"value": "a.*"},
                "with": {"name": "a", "value": {"select": {"value": 1}}},
            },
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_77(self):
        sql = """CACHE LAZY TABLE x AS WITH a AS (SELECT 1) SELECT a.* FROM a"""
        result = parse(sql)
        expected = {"cache": {
            "lazy": True,
            "name": "x",
            "query": {
                "from": "a",
                "select": {"value": "a.*"},
                "with": {"name": "a", "value": {"select": {"value": 1}}},
            },
        }}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_78(self):
        sql = """CACHE TABLE x AS WITH a AS (SELECT 1) SELECT a.* FROM a"""
        result = parse(sql)
        expected = {"cache": {
            "name": "x",
            "query": {
                "from": "a",
                "select": {"value": "a.*"},
                "with": {"name": "a", "value": {"select": {"value": 1}}},
            },
        }}
        self.assertEqual(result, expected)

    @skip("does not pass yet")
    def test_issue_46_sqlglot_79(self):
        sql = """ALTER TYPE electronic_mail RENAME TO email"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_80(self):
        sql = """DELETE FROM x WHERE y > 1"""
        result = parse(sql)
        expected = {"delete": "x", "where": {"gt": ["y", 1]}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_81(self):
        sql = """DROP TABLE a"""
        result = parse(sql)
        expected = {"drop": {"table": "a"}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_82(self):
        sql = """DROP TABLE a.b"""
        result = parse(sql)
        expected = {"drop": {"table": "a.b"}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_83(self):
        sql = """DROP TABLE IF EXISTS a"""
        result = parse(sql)
        expected = {"drop": {"if_exists": True, "table": "a"}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_84(self):
        sql = """DROP TABLE IF EXISTS a.b"""
        result = parse(sql)
        expected = {"drop": {"if_exists": True, "table": "a.b"}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_85(self):
        sql = """DROP VIEW a"""
        result = parse(sql)
        expected = {"drop": {"view": "a"}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_86(self):
        sql = """DROP VIEW a.b"""
        result = parse(sql)
        expected = {"drop": {"view": "a.b"}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_87(self):
        sql = """DROP VIEW IF EXISTS a"""
        result = parse(sql)
        expected = {"drop": {"if_exists": True, "view": "a"}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_88(self):
        sql = """DROP VIEW IF EXISTS a.b"""
        result = parse(sql)
        expected = {"drop": {"if_exists": True, "view": "a.b"}}
        self.assertEqual(result, expected)

    @skip("does not pass yet")
    def test_issue_46_sqlglot_89(self):
        sql = """SHOW TABLES"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    @skip("does not pass yet")
    def test_issue_46_sqlglot_90(self):
        sql = """EXPLAIN SELECT * FROM x"""
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_91(self):
        sql = """INSERT INTO TABLE x SELECT * FROM y"""
        result = parse(sql)
        expected = {"insert": "x", "query": {"from": "y", "select": "*"}}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_92(self):
        sql = """INSERT INTO TABLE x.z IF EXISTS SELECT * FROM y"""
        result = parse(sql)
        expected = {
            "insert": "x.z",
            "if_exists": True,
            "query": {"from": "y", "select": "*"},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_93(self):
        sql = """INSERT INTO TABLE x VALUES (1, 'a', 2.0)"""
        result = parse(sql)
        expected = {
            "insert": "x",
            "query": {"select": [{"value": 1}, {"value": {"literal": "a"}}, {"value": 2.0}]},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_94(self):
        sql = """INSERT INTO TABLE x VALUES (1, 'a', 2.0), (1, 'a', 3.0), (X(), y[1], z.x)"""
        result = parse(sql)
        expected = {
            "insert": "x",
            "query": {"union_all": [
                {"select": [{"value": 1}, {"value": {"literal": "a"}}, {"value": 2.0}]},
                {"select": [{"value": 1}, {"value": {"literal": "a"}}, {"value": 3.0}]},
                {"select": [{"value": {"x": {}}}, {"value": {"get": ["y", 1]}}, {"value": "z.x"}]},
            ]},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_95(self):
        sql = """INSERT OVERWRITE TABLE x IF EXISTS SELECT * FROM y"""
        result = parse(sql)
        expected = {
            "insert": "x",
            "if_exists": True,
            "overwrite": True,
            "query": {"from": "y", "select": "*"},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_96(self):
        sql = """INSERT OVERWRITE TABLE a.b IF EXISTS SELECT * FROM y"""
        result = parse(sql)
        expected = {
            "insert": "a.b",
            "if_exists": True,
            "overwrite": True,
            "query": {"from": "y", "select": "*"},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_97(self):
        sql = """UPDATE tbl_name SET foo = 123"""
        result = parse(sql)
        expected = {"set": {"foo": 123}, "update": "tbl_name"}
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_98(self):
        sql = """UPDATE tbl_name SET foo = 123, bar = 345"""
        result = parse(sql)
        expected = {
            "set": {"bar": 345, "foo": 123},
            "update": "tbl_name",
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_99(self):
        sql = """UPDATE db.tbl_name SET foo = 123 WHERE tbl_name.bar = 234"""
        result = parse(sql)
        expected = {
            "set": {"foo": 123},
            "update": "db.tbl_name",
            "where": {"eq": ["tbl_name.bar", 234]},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_100(self):
        sql = """UPDATE db.tbl_name SET foo = 123, foo_1 = 234 WHERE tbl_name.bar = 234"""
        result = parse(sql)
        expected = {
            "set": {"foo": 123, "foo_1": 234},
            "update": "db.tbl_name",
            "where": {"eq": ["tbl_name.bar", 234]},
        }
        self.assertEqual(result, expected)

    def test_issue_46_sqlglot_101(self):
        sql = """DROP temporary TABLE a"""
        result = parse(sql)
        expected = {"drop": {"temporary": True, "table": "a"}}
        self.assertEqual(result, expected)
