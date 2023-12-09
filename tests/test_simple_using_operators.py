# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from unittest import TestCase

from mo_sql_parsing import parse as sql_parse, normal_op
from tests.util import assertRaises

parse = lambda s: sql_parse(s, calls=normal_op)


class TestSimpleUsingOperators(TestCase):
    def test_two_tables(self):
        result = parse("SELECT * from XYZZY, ABC")
        expected = {"from": ["XYZZY", "ABC"], "select": "*"}
        self.assertEqual(result, expected)

    def test_dot_table_name(self):
        result = parse("select * from SYS.XYZZY")
        expected = {"from": "SYS.XYZZY", "select": "*"}
        self.assertEqual(result, expected)

    def test_select_one_column(self):
        result = parse("Select A from dual")
        expected = {"select": {"value": "A"}, "from": "dual"}
        self.assertEqual(result, expected)

    def test_select_quote(self):
        result = parse("Select '''' from dual")
        expected = {"select": {"value": {"literal": "'"}}, "from": "dual"}
        self.assertEqual(result, expected)

    def test_select_quoted_name(self):
        result = parse('Select a "@*#&", b as test."g.g".c from dual')
        expected = {
            "select": [{"name": "@*#&", "value": "a"}, {"name": "test.g..g.c", "value": "b"}],
            "from": "dual",
        }
        self.assertEqual(result, expected)

    def test_select_expression(self):
        #                         1         2         3         4         5         6
        #               0123456789012345678901234567890123456789012345678901234567890123456789
        result = parse("SELECT a + b/2 + 45*c + (2/d) from dual")
        expected = {
            "from": "dual",
            "select": {"value": {
                "args": [
                    "a",
                    {"args": ["b", 2], "op": "div"},
                    {"args": [45, "c"], "op": "mul"},
                    {"args": [2, "d"], "op": "div"},
                ],
                "op": "add",
            }},
        }
        self.assertEqual(result, expected)

    def test_select_underscore_name(self):
        #                         1         2         3         4         5         6
        #               0123456789012345678901234567890123456789012345678901234567890123456789
        result = parse("select _id from dual")
        expected = {"select": {"value": "_id"}, "from": "dual"}
        self.assertEqual(result, expected)

    def test_select_dots_names(self):
        #                         1         2         3         4         5         6
        #               0123456789012345678901234567890123456789012345678901234567890123456789
        result = parse("select a.b.c._d from dual")
        expected = {"select": {"value": "a.b.c._d"}, "from": "dual"}
        self.assertEqual(result, expected)

    def test_select_many_column(self):
        result = parse("Select a, b, c from dual")
        expected = {
            "select": [{"value": "a"}, {"value": "b"}, {"value": "c"}],
            "from": "dual",
        }
        self.assertEqual(result, expected)

    def test_bad_select1(self):
        with self.assertRaises(Exception):
            # was 'Expecting select'
            parse("se1ect A, B, C from dual")

    def test_bad_select2(self):
        with self.assertRaises(Exception):
            # was 'Expecting {{expression1 + [{[as] + column_name1}]}'
            parse("Select &&& FROM dual")

    def test_bad_from(self):
        assertRaises("(at char 20", lambda: parse("select A, B, C frum dual"))

    def test_incomplete1(self):
        with self.assertRaises(Exception):
            # was 'Expecting {{expression1 + [{[as] + column_name1}]}}'
            parse("SELECT")

    def test_incomplete2(self):
        assertRaises("", lambda: parse("SELECT * FROM"))

    def test_where_neq(self):
        #                         1         2         3         4         5         6
        #               0123456789012345678901234567890123456789012345678901234567890123456789
        result = parse("SELECT * FROM dual WHERE a<>'test'")
        expected = {
            "from": "dual",
            "select": "*",
            "where": {"args": ["a", {"literal": "test"}], "op": "neq"},
        }
        self.assertEqual(result, expected)

    def test_where_in(self):
        result = parse("SELECT a FROM dual WHERE a in ('r', 'g', 'b')")
        expected = {
            "from": "dual",
            "select": {"value": "a"},
            "where": {"args": ["a", {"literal": ["r", "g", "b"]}], "op": "in"},
        }
        self.assertEqual(result, expected)

    def test_where_in_and_in(self):
        #                         1         2         3         4         5         6
        #               0123456789012345678901234567890123456789012345678901234567890123456789
        result = parse("SELECT a FROM dual WHERE a in ('r', 'g', 'b') AND b in (10, 11, 12)")
        expected = {
            "from": "dual",
            "select": {"value": "a"},
            "where": {
                "args": [
                    {"args": ["a", {"literal": ["r", "g", "b"]}], "op": "in"},
                    {"args": ["b", [10, 11, 12]], "op": "in"},
                ],
                "op": "and",
            },
        }
        self.assertEqual(result, expected)

    def test_eq(self):
        result = parse("SELECT a, b FROM t1, t2 WHERE t1.a=t2.b")
        expected = {
            "from": ["t1", "t2"],
            "select": [{"value": "a"}, {"value": "b"}],
            "where": {"args": ["t1.a", "t2.b"], "op": "eq"},
        }
        self.assertEqual(result, expected)

    def test_is_null(self):
        result = parse("SELECT a, b FROM t1 WHERE t1.a IS NULL")
        expected = {
            "from": "t1",
            "select": [{"value": "a"}, {"value": "b"}],
            "where": {"args": ["t1.a"], "op": "missing"},
        }
        self.assertEqual(result, expected)

    def test_is_not_null(self):
        result = parse("SELECT a, b FROM t1 WHERE t1.a IS NOT NULL")
        expected = {
            "from": "t1",
            "select": [{"value": "a"}, {"value": "b"}],
            "where": {"args": ["t1.a"], "op": "exists"},
        }
        self.assertEqual(result, expected)

    def test_groupby(self):
        result = parse("select a, count(1) as b from mytable group by a")
        expected = {
            "from": "mytable",
            "groupby": {"value": "a"},
            "select": [{"value": "a"}, {"name": "b", "value": {"args": [1], "op": "count"}}],
        }
        self.assertEqual(result, expected)

    def test_function(self):
        #               0         1         2
        #               0123456789012345678901234567890
        result = parse("select count(1) from mytable")
        expected = {
            "from": "mytable",
            "select": {"value": {"args": [1], "op": "count"}},
        }
        self.assertEqual(result, expected)

    def test_function_underscore(self):
        #               0         1         2
        #               0123456789012345678901234567890
        result = parse("select DATE_TRUNC('2019-04-12', WEEK) from mytable")
        expected = {
            "from": "mytable",
            "select": {"value": {"args": [{"literal": "2019-04-12"}, "WEEK"], "op": "date_trunc"}},
        }
        self.assertEqual(result, expected)

    def test_order_by(self):
        result = parse("select count(1) from dual order by a")
        expected = {
            "from": "dual",
            "orderby": {"value": "a"},
            "select": {"value": {"args": [1], "op": "count"}},
        }
        self.assertEqual(result, expected)

    def test_order_by_asc(self):
        result = parse("select count(1) from dual order by a asc")
        expected = {
            "from": "dual",
            "orderby": {"sort": "asc", "value": "a"},
            "select": {"value": {"args": [1], "op": "count"}},
        }
        self.assertEqual(result, expected)

    def test_neg_or_precedence(self):
        result = parse("select B,C from table1 where A=-900 or B=100")
        expected = {
            "from": "table1",
            "select": [{"value": "B"}, {"value": "C"}],
            "where": {"args": [{"args": ["A", -900], "op": "eq"}, {"args": ["B", 100], "op": "eq"}], "op": "or"},
        }
        self.assertEqual(result, expected)

    def test_negative_number(self):
        result = parse("select a from table1 where A=-900")
        expected = {
            "from": "table1",
            "select": {"value": "a"},
            "where": {"args": ["A", -900], "op": "eq"},
        }
        self.assertEqual(result, expected)

    def test_like_in_where(self):
        result = parse("select a from table1 where A like '%20%'")
        expected = {
            "from": "table1",
            "select": {"value": "a"},
            "where": {"args": ["A", {"literal": "%20%"}], "op": "like"},
        }
        self.assertEqual(result, expected)

    def test_not_like_in_where(self):
        result = parse("select a from table1 where A not like '%20%'")
        expected = {
            "from": "table1",
            "select": {"value": "a"},
            "where": {"args": ["A", {"literal": "%20%"}], "op": "not_like"},
        }
        self.assertEqual(result, expected)

    def test_like_in_select(self):
        #               0         1         2         3         4         5         6
        #               0123456789012345678901234567890123456789012345678901234567890123456789
        result = parse("select case when A like 'bb%' then 1 else 0 end as bb from table1")
        expected = {
            "from": "table1",
            "select": {
                "name": "bb",
                "value": {
                    "args": [
                        {
                            "args": [{"args": ["A", {"literal": "bb%"}], "op": "like"}],
                            "kwargs": {"then": 1},
                            "op": "when",
                        },
                        0,
                    ],
                    "op": "case",
                },
            },
        }
        self.assertEqual(result, expected)

    def test_switch_else(self):
        result = parse("select case table0.y1 when 'a' then 1 else 0 end from table0")
        expected = {
            "from": "table0",
            "select": {"value": {
                "args": [
                    {
                        "args": [{"args": ["table0.y1", {"literal": "a"}], "op": "eq"}],
                        "kwargs": {"then": 1},
                        "op": "when",
                    },
                    0,
                ],
                "op": "case",
            }},
        }
        self.assertEqual(result, expected)

    def test_not_like_in_select(self):
        result = parse("select case when A not like 'bb%' then 1 else 0 end as bb from table1")
        expected = {
            "from": "table1",
            "select": {
                "name": "bb",
                "value": {
                    "args": [
                        {
                            "args": [{"args": ["A", {"literal": "bb%"}], "op": "not_like"}],
                            "kwargs": {"then": 1},
                            "op": "when",
                        },
                        0,
                    ],
                    "op": "case",
                },
            },
        }
        self.assertEqual(result, expected)

    def test_like_from_pr16(self):
        result = parse("select * from trade where school LIKE '%shool' and name='abc' and id IN ('1','2')")
        expected = {
            "from": "trade",
            "select": "*",
            "where": {
                "args": [
                    {"args": ["school", {"literal": "%shool"}], "op": "like"},
                    {"args": ["name", {"literal": "abc"}], "op": "eq"},
                    {"args": ["id", {"literal": ["1", "2"]}], "op": "in"},
                ],
                "op": "and",
            },
        }
        self.assertEqual(result, expected)

    def test_rlike_in_where(self):
        result = parse("select a from table1 where A rlike '.*20.*'")
        expected = {
            "from": "table1",
            "select": {"value": "a"},
            "where": {"args": ["A", {"literal": ".*20.*"}], "op": "rlike"},
        }
        self.assertEqual(result, expected)

    def test_not_rlike_in_where(self):
        result = parse("select a from table1 where A not rlike '.*20.*'")
        expected = {
            "from": "table1",
            "select": {"value": "a"},
            "where": {"args": ["A", {"literal": ".*20.*"}], "op": "not_rlike"},
        }
        self.assertEqual(result, expected)

    def test_rlike_in_select(self):
        result = parse("select case when A rlike 'bb.*' then 1 else 0 end as bb from table1")
        expected = {
            "from": "table1",
            "select": {
                "name": "bb",
                "value": {
                    "args": [
                        {
                            "args": [{"args": ["A", {"literal": "bb.*"}], "op": "rlike"}],
                            "kwargs": {"then": 1},
                            "op": "when",
                        },
                        0,
                    ],
                    "op": "case",
                },
            },
        }
        self.assertEqual(result, expected)

    def test_not_rlike_in_select(self):
        result = parse("select case when A not rlike 'bb.*' then 1 else 0 end as bb from table1")
        expected = {
            "from": "table1",
            "select": {
                "name": "bb",
                "value": {
                    "args": [
                        {
                            "args": [{"args": ["A", {"literal": "bb.*"}], "op": "not_rlike"}],
                            "kwargs": {"then": 1},
                            "op": "when",
                        },
                        0,
                    ],
                    "op": "case",
                },
            },
        }
        self.assertEqual(result, expected)

    def test_in_expression(self):
        result = parse("select * from task where repo.branch.name in ('try', 'mozilla-central')")
        expected = {
            "from": "task",
            "select": "*",
            "where": {"args": ["repo.branch.name", {"literal": ["try", "mozilla-central"]}], "op": "in"},
        }
        self.assertEqual(result, expected)

    def test_not_in_expression(self):
        result = parse("select * from task where repo.branch.name not in ('try', 'mozilla-central')")
        expected = {
            "from": "task",
            "select": "*",
            "where": {"args": ["repo.branch.name", {"literal": ["try", "mozilla-central"]}], "op": "nin"},
        }
        self.assertEqual(result, expected)

    def test_joined_table_name(self):
        result = parse("SELECT * FROM table1 t1 JOIN table3 t3 ON t1.id = t3.id")

        expected = {
            "from": [
                {"name": "t1", "value": "table1"},
                {"join": {"name": "t3", "value": "table3"}, "on": {"args": ["t1.id", "t3.id"], "op": "eq"}},
            ],
            "select": "*",
        }
        self.assertEqual(result, expected)

    def test_not_equal(self):
        #               0         1         2         3         4         5         6        7          8
        #               012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        result = parse("select * from task where build.product is not null and build.product!='firefox'")

        expected = {
            "from": "task",
            "select": "*",
            "where": {
                "args": [
                    {"args": ["build.product"], "op": "exists"},
                    {"args": ["build.product", {"literal": "firefox"}], "op": "neq"},
                ],
                "op": "and",
            },
        }
        self.assertEqual(result, expected)

    def test_pr19(self):
        result = parse("select empid from emp where ename like 's%' ")
        expected = {
            "from": "emp",
            "select": {"value": "empid"},
            "where": {"args": ["ename", {"literal": "s%"}], "op": "like"},
        }
        self.assertEqual(result, expected)

    def test_left_join(self):
        result = parse("SELECT t1.field1 FROM t1 LEFT JOIN t2 ON t1.id = t2.id")
        expected = {
            "from": ["t1", {"left join": "t2", "on": {"args": ["t1.id", "t2.id"], "op": "eq"}}],
            "select": {"value": "t1.field1"},
        }
        self.assertEqual(result, expected)

    def test_multiple_left_join(self):
        result = parse("SELECT t1.field1 FROM t1 LEFT JOIN t2 ON t1.id = t2.id LEFT JOIN t3 ON t1.id = t3.id")
        expected = {
            "from": [
                "t1",
                {"left join": "t2", "on": {"args": ["t1.id", "t2.id"], "op": "eq"}},
                {"left join": "t3", "on": {"args": ["t1.id", "t3.id"], "op": "eq"}},
            ],
            "select": {"value": "t1.field1"},
        }
        self.assertEqual(result, expected)

    def test_union(self):
        result = parse("SELECT b FROM t6 UNION SELECT '3' AS x ORDER BY x")
        expected = {
            "from": {"union": [
                {"from": "t6", "select": {"value": "b"}},
                {"select": {"value": {"literal": "3"}, "name": "x"}},
            ]},
            "orderby": {"value": "x"},
        }
        self.assertEqual(result, expected)

    def test_left_outer_join(self):
        result = parse("SELECT t1.field1 FROM t1 LEFT OUTER JOIN t2 ON t1.id = t2.id")
        expected = {
            "from": ["t1", {"left outer join": "t2", "on": {"args": ["t1.id", "t2.id"], "op": "eq"}}],
            "select": {"value": "t1.field1"},
        }
        self.assertEqual(result, expected)

    def test_right_join(self):
        result = parse("SELECT t1.field1 FROM t1 RIGHT JOIN t2 ON t1.id = t2.id")
        expected = {
            "from": ["t1", {"on": {"args": ["t1.id", "t2.id"], "op": "eq"}, "right join": "t2"}],
            "select": {"value": "t1.field1"},
        }
        self.assertEqual(result, expected)

    def test_right_outer_join(self):
        result = parse("SELECT t1.field1 FROM t1 RIGHT OUTER JOIN t2 ON t1.id = t2.id")
        expected = {
            "from": ["t1", {"on": {"args": ["t1.id", "t2.id"], "op": "eq"}, "right outer join": "t2"}],
            "select": {"value": "t1.field1"},
        }
        self.assertEqual(result, expected)

    def test_full_join(self):
        result = parse("SELECT t1.field1 FROM t1 FULL JOIN t2 ON t1.id = t2.id")
        expected = {
            "from": ["t1", {"full join": "t2", "on": {"args": ["t1.id", "t2.id"], "op": "eq"}}],
            "select": {"value": "t1.field1"},
        }
        self.assertEqual(result, expected)

    def test_full_outer_join(self):
        result = parse("SELECT t1.field1 FROM t1 FULL OUTER JOIN t2 ON t1.id = t2.id")
        expected = {
            "from": ["t1", {"full outer join": "t2", "on": {"args": ["t1.id", "t2.id"], "op": "eq"}}],
            "select": {"value": "t1.field1"},
        }
        self.assertEqual(result, expected)

    def test_join_via_using(self):
        result = parse("SELECT t1.field1 FROM t1 JOIN t2 USING (id)")
        expected = {
            "select": {"value": "t1.field1"},
            "from": ["t1", {"join": "t2", "using": "id"}],
        }
        self.assertEqual(result, expected)

    def test_where_between(self):
        result = parse("SELECT a FROM dual WHERE a BETWEEN 1 and 2")
        expected = {
            "from": "dual",
            "select": {"value": "a"},
            "where": {"args": ["a", 1, 2], "op": "between"},
        }
        self.assertEqual(result, expected)

    def test_where_not_between(self):
        result = parse("SELECT a FROM dual WHERE a NOT BETWEEN 1 and 2")
        expected = {
            "from": "dual",
            "select": {"value": "a"},
            "where": {"args": ["a", 1, 2], "op": "not_between"},
        }
        self.assertEqual(result, expected)

    def test_select_from_select(self):
        #               0         1         2         3
        #               0123456789012345678901234567890123456789
        result = parse("SELECT b.a FROM ( SELECT 2 AS a ) b")
        expected = {
            "select": {"value": "b.a"},
            "from": {"name": "b", "value": {"select": {"value": 2, "name": "a"}}},
        }
        self.assertEqual(result, expected)

    def test_unicode_strings(self):
        result = parse("select '0:普通,1:旗舰' from mobile")
        expected = {"select": {"value": {"literal": "0:普通,1:旗舰"}}, "from": "mobile"}
        self.assertEqual(result, expected)

    def test_issue68(self):
        result = parse("select deflate(sum(int(mobile_price.price))) from mobile")
        expected = {
            "from": "mobile",
            "select": {"value": {
                "args": [{"args": [{"args": ["mobile_price.price"], "op": "int"}], "op": "sum"}],
                "op": "deflate",
            }},
        }
        self.assertEqual(result, expected)

    def test_issue_90(self):
        result = parse(
            """
        SELECT MIN(cn.name) AS from_company
        FROM company_name AS cn, company_type AS ct, keyword AS k, movie_link AS ml, title AS t
        WHERE cn.country_code !='[pl]' AND ct.kind IS NOT NULL AND t.production_year > 1950 AND ml.movie_id = t.id
        """
        )
        expected = {
            "from": [
                {"name": "cn", "value": "company_name"},
                {"name": "ct", "value": "company_type"},
                {"name": "k", "value": "keyword"},
                {"name": "ml", "value": "movie_link"},
                {"name": "t", "value": "title"},
            ],
            "select": {"name": "from_company", "value": {"args": ["cn.name"], "op": "min"}},
            "where": {
                "args": [
                    {"args": ["cn.country_code", {"literal": "[pl]"}], "op": "neq"},
                    {"args": ["ct.kind"], "op": "exists"},
                    {"args": ["t.production_year", 1950], "op": "gt"},
                    {"args": ["ml.movie_id", "t.id"], "op": "eq"},
                ],
                "op": "and",
            },
        }
        self.assertEqual(result, expected)

    def test_issue_68a(self):
        sql = """
        SELECT *
        FROM aka_name AS an, cast_info AS ci, info_type AS it, link_type AS lt, movie_link AS ml, name AS n, person_info AS pi, title AS t
        WHERE
            an.name  is not NULL
            and (an.name LIKE '%a%' or an.name LIKE 'A%')
            AND it.info ='mini biography'
            AND lt.link  in ('references', 'referenced in', 'features', 'featured in')
            AND n.name_pcode_cf BETWEEN 'A' AND 'F'
            AND (n.gender = 'm' OR (n.gender = 'f' AND n.name LIKE 'A%'))
            AND pi.note  is not NULL
            AND t.production_year BETWEEN 1980 AND 2010
            AND n.id = an.person_id
            AND n.id = pi.person_id
            AND ci.person_id = n.id
            AND t.id = ci.movie_id
            AND ml.linked_movie_id = t.id
            AND lt.id = ml.link_type_id
            AND it.id = pi.info_type_id
            AND pi.person_id = an.person_id
            AND pi.person_id = ci.person_id
            AND an.person_id = ci.person_id
            AND ci.movie_id = ml.linked_movie_id
        """
        result = parse(sql)
        expected = {
            "from": [
                {"name": "an", "value": "aka_name"},
                {"name": "ci", "value": "cast_info"},
                {"name": "it", "value": "info_type"},
                {"name": "lt", "value": "link_type"},
                {"name": "ml", "value": "movie_link"},
                {"name": "n", "value": "name"},
                {"name": "pi", "value": "person_info"},
                {"name": "t", "value": "title"},
            ],
            "select": "*",
            "where": {
                "args": [
                    {"args": ["an.name"], "op": "exists"},
                    {
                        "args": [
                            {"args": ["an.name", {"literal": "%a%"}], "op": "like"},
                            {"args": ["an.name", {"literal": "A%"}], "op": "like"},
                        ],
                        "op": "or",
                    },
                    {"args": ["it.info", {"literal": "mini biography"}], "op": "eq"},
                    {
                        "args": ["lt.link", {"literal": ["references", "referenced in", "features", "featured in"]}],
                        "op": "in",
                    },
                    {"args": ["n.name_pcode_cf", {"literal": "A"}, {"literal": "F"}], "op": "between"},
                    {
                        "args": [
                            {"args": ["n.gender", {"literal": "m"}], "op": "eq"},
                            {
                                "args": [
                                    {"args": ["n.gender", {"literal": "f"}], "op": "eq"},
                                    {"args": ["n.name", {"literal": "A%"}], "op": "like"},
                                ],
                                "op": "and",
                            },
                        ],
                        "op": "or",
                    },
                    {"args": ["pi.note"], "op": "exists"},
                    {"args": ["t.production_year", 1980, 2010], "op": "between"},
                    {"args": ["n.id", "an.person_id"], "op": "eq"},
                    {"args": ["n.id", "pi.person_id"], "op": "eq"},
                    {"args": ["ci.person_id", "n.id"], "op": "eq"},
                    {"args": ["t.id", "ci.movie_id"], "op": "eq"},
                    {"args": ["ml.linked_movie_id", "t.id"], "op": "eq"},
                    {"args": ["lt.id", "ml.link_type_id"], "op": "eq"},
                    {"args": ["it.id", "pi.info_type_id"], "op": "eq"},
                    {"args": ["pi.person_id", "an.person_id"], "op": "eq"},
                    {"args": ["pi.person_id", "ci.person_id"], "op": "eq"},
                    {"args": ["an.person_id", "ci.person_id"], "op": "eq"},
                    {"args": ["ci.movie_id", "ml.linked_movie_id"], "op": "eq"},
                ],
                "op": "and",
            },
        }
        self.assertEqual(result, expected)

    def test_issue_68b(self):
        #      0         1         2         3         4         5         6         7         8         9
        #      012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        sql = "SELECT COUNT(*) AS CNT FROM test.tb WHERE (id IN (unhex('1'),unhex('2'))) AND  status=1;"
        result = parse(sql)
        expected = {
            "from": "test.tb",
            "select": {"name": "CNT", "value": {"args": ["*"], "op": "count"}},
            "where": {
                "args": [
                    {
                        "args": [
                            "id",
                            [
                                {"args": [{"literal": "1"}], "op": "unhex"},
                                {"args": [{"literal": "2"}], "op": "unhex"},
                            ],
                        ],
                        "op": "in",
                    },
                    {"args": ["status", 1], "op": "eq"},
                ],
                "op": "and",
            },
        }
        self.assertEqual(result, expected)

    def test_binary_and(self):
        sql = "SELECT * FROM t WHERE  c & 4;"
        result = parse(sql)
        expected = {
            "from": "t",
            "select": "*",
            "where": {"args": ["c", 4], "op": "binary_and"},
        }
        self.assertEqual(result, expected)

    def test_binary_or(self):
        sql = "SELECT * FROM t WHERE c | 4;"
        result = parse(sql)
        expected = {
            "from": "t",
            "select": "*",
            "where": {"args": ["c", 4], "op": "binary_or"},
        }
        self.assertEqual(result, expected)

    def test_binary_not(self):
        #      0         1         2
        #      012345678901234567890123456789
        sql = "SELECT * FROM t WHERE ~c;"
        result = parse(sql)
        expected = {
            "from": "t",
            "select": "*",
            "where": {"args": ["c"], "op": "binary_not"},
        }
        self.assertEqual(result, expected)

    def test_or_and(self):
        sql = "SELECT * FROM dual WHERE a OR b AND c"
        result = parse(sql)
        expected = {
            "from": "dual",
            "select": "*",
            "where": {"args": ["a", {"args": ["b", "c"], "op": "and"}], "op": "or"},
        }
        self.assertEqual(result, expected)

    def test_and_or(self):
        sql = "SELECT * FROM dual WHERE a AND b or c"
        result = parse(sql)
        expected = {
            "from": "dual",
            "select": "*",
            "where": {"args": [{"args": ["a", "b"], "op": "and"}, "c"], "op": "or"},
        }
        self.assertEqual(result, expected)

    def test_underscore_function1(self):
        sql = "SELECT _()"
        result = parse(sql)
        expected = {"select": {"value": {"op": "_"}}}
        self.assertEqual(result, expected)

    def test_underscore_function2(self):
        sql = "SELECT _a(a$b)"
        result = parse(sql)
        expected = {"select": {"value": {"args": ["a$b"], "op": "_a"}}}
        self.assertEqual(result, expected)

    def test_underscore_function3(self):
        sql = "SELECT _$$_(a, b$)"
        result = parse(sql)
        expected = {"select": {"value": {"args": ["a", "b$"], "op": "_$$_"}}}
        self.assertEqual(result, expected)

    def test_union_all1(self):
        #               0         1         2         3         4         5         6         7         8         9
        #               012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        result = parse("SELECT b FROM t6 UNION ALL SELECT '3' AS x ORDER BY x")
        expected = {
            "from": {"union_all": [
                {"from": "t6", "select": {"value": "b"}},
                {"select": {"value": {"literal": "3"}, "name": "x"}},
            ]},
            "orderby": {"value": "x"},
        }
        self.assertEqual(result, expected)

    def test_union_all2(self):
        result = parse("SELECT b UNION ALL SELECT c")
        expected = {"union_all": [{"select": {"value": "b"}}, {"select": {"value": "c"}}]}
        self.assertEqual(result, expected)

    def test_issue106(self):
        result = parse(
            """
            SELECT *
            FROM MyTable
            GROUP BY Col
            HAVING AVG(X) >= 2
            AND AVG(X) <= 4
            OR AVG(X) = 5;
        """
        )
        expected = {
            "from": "MyTable",
            "groupby": {"value": "Col"},
            "having": {
                "args": [
                    {
                        "args": [
                            {"args": [{"args": ["X"], "op": "avg"}, 2], "op": "gte"},
                            {"args": [{"args": ["X"], "op": "avg"}, 4], "op": "lte"},
                        ],
                        "op": "and",
                    },
                    {"args": [{"args": ["X"], "op": "avg"}, 5], "op": "eq"},
                ],
                "op": "or",
            },
            "select": "*",
        }
        self.assertEqual(result, expected)

    def test_issue97_function_names(self):
        sql = "SELECT ST_AsText(ST_MakePoint(174, -36));"
        result = parse(sql)
        expected = {"select": {"value": {"args": [{"args": [174, -36], "op": "st_makepoint"}], "op": "st_astext"}}}
        self.assertEqual(result, expected)

    def test_issue91_order_of_operations1(self):
        sql = "select 5-4+2"
        result = parse(sql)
        expected = {"select": {"value": {"args": [{"args": [5, 4], "op": "sub"}, 2], "op": "add"}}}
        self.assertEqual(result, expected)

    def test_issue91_order_of_operations2(self):
        sql = "select 5/4*2"
        result = parse(sql)
        expected = {"select": {"value": {"args": [{"args": [5, 4], "op": "div"}, 2], "op": "mul"}}}
        self.assertEqual(result, expected)

    def test_issue_92(self):
        sql = "SELECT * FROM `movies`"
        result = parse(sql)
        expected = {"select": "*", "from": "movies"}
        self.assertEqual(result, expected)

    def test_with_clause(self):
        sql = (
            " WITH dept_count AS ("
            "     SELECT deptno, COUNT(*) AS dept_count"
            "     FROM emp"
            "     GROUP BY deptno"
            ")"
            " SELECT "
            "     e.ename AS employee_name,"
            "     dc1.dept_count AS emp_dept_count,"
            "     m.ename AS manager_name,"
            "     dc2.dept_count AS mgr_dept_count"
            " FROM "
            "     emp e,"
            "     dept_count dc1,"
            "     emp m,"
            "     dept_count dc2"
            " WHERE "
            "     e.deptno = dc1.deptno"
            "     AND e.mgr = m.empno"
            "     AND m.deptno = dc2.deptno;"
        )
        result = parse(sql)
        expected = {
            "from": [
                {"name": "e", "value": "emp"},
                {"name": "dc1", "value": "dept_count"},
                {"name": "m", "value": "emp"},
                {"name": "dc2", "value": "dept_count"},
            ],
            "select": [
                {"name": "employee_name", "value": "e.ename"},
                {"name": "emp_dept_count", "value": "dc1.dept_count"},
                {"name": "manager_name", "value": "m.ename"},
                {"name": "mgr_dept_count", "value": "dc2.dept_count"},
            ],
            "where": {
                "args": [
                    {"args": ["e.deptno", "dc1.deptno"], "op": "eq"},
                    {"args": ["e.mgr", "m.empno"], "op": "eq"},
                    {"args": ["m.deptno", "dc2.deptno"], "op": "eq"},
                ],
                "op": "and",
            },
            "with": {
                "name": "dept_count",
                "value": {
                    "from": "emp",
                    "groupby": {"value": "deptno"},
                    "select": [{"value": "deptno"}, {"name": "dept_count", "value": {"args": ["*"], "op": "count"}}],
                },
            },
        }

        self.assertEqual(result, expected)

    def test_2with_clause(self):
        #    0         1         2         3         4         5         6         7         8         9
        #    012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        sql = " WITH a AS (SELECT 1), b AS (SELECT 2) SELECT * FROM a UNION ALL SELECT * FROM b"
        result = parse(sql)
        expected = {
            "union_all": [{"from": "a", "select": "*"}, {"from": "b", "select": "*"}],
            "with": [
                {"name": "a", "value": {"select": {"value": 1}}},
                {"name": "b", "value": {"select": {"value": 2}}},
            ],
        }
        self.assertEqual(result, expected)

    def test_issue_38a(self):
        sql = "SELECT a IN ('abc',3,'def')"
        result = parse(sql)
        expected = {"select": {"value": {"args": ["a", {"literal": ["abc", 3, "def"]}], "op": "in"}}}
        self.assertEqual(result, expected)

    def test_issue_38b(self):
        sql = "SELECT a IN (abc,3,'def')"
        result = parse(sql)
        expected = {"select": {"value": {"args": ["a", ["abc", 3, {"literal": "def"}]], "op": "in"}}}
        self.assertEqual(result, expected)

    def test_issue_107_recursion(self):
        sql = (
            " SELECT city_name"
            " FROM city"
            " WHERE population = ("
            "     SELECT MAX(population)"
            "     FROM city"
            "     WHERE state_name IN ("
            "         SELECT state_name"
            "         FROM state"
            "         WHERE area = (SELECT MIN(area) FROM state)"
            "     )"
            " )"
        )
        result = parse(sql)
        expected = {
            "from": "city",
            "select": {"value": "city_name"},
            "where": {
                "args": [
                    "population",
                    {
                        "from": "city",
                        "select": {"value": {"args": ["population"], "op": "max"}},
                        "where": {
                            "args": [
                                "state_name",
                                {
                                    "from": "state",
                                    "select": {"value": "state_name"},
                                    "where": {
                                        "args": [
                                            "area",
                                            {"from": "state", "select": {"value": {"args": ["area"], "op": "min"}}},
                                        ],
                                        "op": "eq",
                                    },
                                },
                            ],
                            "op": "in",
                        },
                    },
                ],
                "op": "eq",
            },
        }
        self.assertEqual(result, expected)

    def test_issue_95(self):
        #      0         1         2         3         4         5         6         7         8         9
        #      012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        sql = "select * from some_table.some_function('parameter', 1, some_col)"
        result = parse(sql)
        expected = {
            "from": {"args": [{"literal": "parameter"}, 1, "some_col"], "op": "some_table.some_function"},
            "select": "*",
        }
        self.assertEqual(result, expected)

    def test_date(self):
        sql = "select DATE '2020 01 25'"
        result = parse(sql)
        expected = {"select": {"value": {"args": [{"literal": "2020 01 25"}], "op": "date"}}}
        self.assertEqual(result, expected)

    def test_interval(self):
        sql = "select INTErval 30.5 monthS"
        result = parse(sql)
        expected = {"select": {"value": {"args": [30.5, "month"], "op": "interval"}}}
        self.assertEqual(result, expected)

    def test_date_less_interval(self):
        sql = "select DATE '2020 01 25' - interval 4 seconds"
        result = parse(sql)
        expected = {"select": {"value": {
            "args": [{"args": [{"literal": "2020 01 25"}], "op": "date"}, {"args": [4, "second"], "op": "interval"}],
            "op": "sub",
        }}}
        self.assertEqual(result, expected)

    def test_issue_141(self):
        sql = "select name from table order by age limit 1 offset 3"
        result = parse(sql)
        expected = {
            "select": {"value": "name"},
            "from": "table",
            "orderby": {"value": "age"},
            "limit": 1,
            "offset": 3,
        }
        self.assertEqual(result, expected)

    def test_issue_144(self):
        sql = (
            "SELECT count(url) FROM crawl_urls WHERE ((http_status_code = 200 AND"
            " meta_redirect = FALSE AND primary_page = TRUE AND indexable = TRUE AND"
            " canonicalized_page = FALSE AND (paginated_page = FALSE OR (paginated_page"
            " = TRUE AND page_1 = TRUE))) AND ((css <> TRUE AND js <> TRUE AND is_image"
            " <> TRUE AND internal = TRUE) AND (header_content_type = 'text/html' OR"
            " header_content_type = ''))) ORDER BY count(url) DESC"
        )
        result = parse(sql)
        expected = {
            "from": "crawl_urls",
            "orderby": {"sort": "desc", "value": {"args": ["url"], "op": "count"}},
            "select": {"value": {"args": ["url"], "op": "count"}},
            "where": {
                "args": [
                    {"args": ["http_status_code", 200], "op": "eq"},
                    {"args": ["meta_redirect", False], "op": "eq"},
                    {"args": ["primary_page", True], "op": "eq"},
                    {"args": ["indexable", True], "op": "eq"},
                    {"args": ["canonicalized_page", False], "op": "eq"},
                    {
                        "args": [
                            {"args": ["paginated_page", False], "op": "eq"},
                            {
                                "args": [
                                    {"args": ["paginated_page", True], "op": "eq"},
                                    {"args": ["page_1", True], "op": "eq"},
                                ],
                                "op": "and",
                            },
                        ],
                        "op": "or",
                    },
                    {"args": ["css", True], "op": "neq"},
                    {"args": ["js", True], "op": "neq"},
                    {"args": ["is_image", True], "op": "neq"},
                    {"args": ["internal", True], "op": "eq"},
                    {
                        "args": [
                            {"args": ["header_content_type", {"literal": "text/html"}], "op": "eq"},
                            {"args": ["header_content_type", {"literal": ""}], "op": "eq"},
                        ],
                        "op": "or",
                    },
                ],
                "op": "and",
            },
        }
        self.assertEqual(result, expected)

    def test_and_w_tuple(self):
        #      0         1         2         3         4         5         6         7         8         9
        #      012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        sql = "SELECT * FROM a WHERE ((a = 1 AND (b=2 AND c=3, False)))"
        result = parse(sql)
        expected = {
            "from": "a",
            "select": "*",
            "where": {
                "args": [
                    {"args": ["a", 1], "op": "eq"},
                    [{"args": [{"args": ["b", 2], "op": "eq"}, {"args": ["c", 3], "op": "eq"}], "op": "and"}, False,],
                ],
                "op": "and",
            },
        }
        self.assertEqual(result, expected)

    def test_and_w_tuple2(self):
        sql = "SELECT ('a', 'b', 'c')"
        result = parse(sql)
        expected = {"select": {"value": {"literal": ["a", "b", "c"]}}}
        self.assertEqual(result, expected)

    def test_null_parameter(self):
        sql = "select DECODE(A, NULL, 'b')"
        result = parse(sql)
        expected = {"select": {"value": {"args": ["A", {"null": {}}, {"literal": "b"}], "op": "decode"}}}
        self.assertEqual(result, expected)

    def test_issue140(self):
        sql = "select rank(*) over (partition by a order by b, c) from tab"
        result = parse(sql)
        expected = {
            "from": "tab",
            "select": {
                "over": {"orderby": [{"value": "b"}, {"value": "c"}], "partitionby": "a"},
                "value": {"args": ["*"], "op": "rank"},
            },
        }
        self.assertEqual(result, expected)

    def test_issue119(self):
        sql = "SELECT 1 + CAST(1 AS INT) result"
        result = parse(sql)
        expected = {"select": {
            "name": "result",
            "value": {"args": [1, {"args": [1, {"op": "int"}], "op": "cast"}], "op": "add"},
        }}
        self.assertEqual(result, expected)

    def test_issue120(self):
        sql = "SELECT DISTINCT Country, City FROM Customers"
        result = parse(sql)
        expected = {
            "from": "Customers",
            "select_distinct": [{"value": "Country"}, {"value": "City"}],
        }
        self.assertEqual(result, expected)

    def test_issue1_of_fork(self):
        #      0         1         2
        #      012345678901234567890123456789
        sql = "SELECT * FROM jobs LIMIT 10"
        result = parse(sql)
        expected = {"from": "jobs", "limit": 10, "select": "*"}
        self.assertEqual(result, expected)

    def test_issue2a_of_fork(self):
        sql = "SELECT COUNT(DISTINCT Y) FROM A "
        result = parse(sql)
        self.assertEqual(
            result, {"from": "A", "select": {"value": {"op": "count", "args": ["Y"], "kwargs": {"distinct": True}}}},
        )

    def test_issue2b_of_fork(self):
        sql = "SELECT COUNT( DISTINCT B, E), A FROM C WHERE D= X GROUP BY A"
        result = parse(sql)
        self.assertEqual(
            result,
            {
                "from": "C",
                "groupby": {"value": "A"},
                "select": [
                    {"value": {"op": "count", "args": ["B", "E"], "kwargs": {"distinct": True}}},
                    {"value": "A"},
                ],
                "where": {"args": ["D", "X"], "op": "eq"},
            },
        )

    def test_orderby_in_window_function(self):
        sql = "select rank(*) over (partition by a order by b, c desc) from tab"
        result = parse(sql)
        self.assertEqual(
            result,
            {
                "from": "tab",
                "select": {
                    "over": {"orderby": [{"value": "b"}, {"sort": "desc", "value": "c"}], "partitionby": "a"},
                    "value": {"args": ["*"], "op": "rank"},
                },
            },
        )

    def test_issue_156a_SDSS_default_multiply(self):
        sql = "SELECT 23e7test "
        result = parse(sql)
        self.assertEqual(result, {"select": {"value": {"mul": [230000000, "test"]}}})

    def test_issue_156a_SDSS(self):
        sql = """
            SELECT TOP 10 u,g,r,i,z,ra,dec, flags_r
            FROM Star
            WHERE
            ra BETWEEN 180 and 181 AND dec BETWEEN -0.5 and 0.5
            AND ((flags_r & 0x10000000) != 0)
            AND ((flags_r & 0x8100000c00a4) = 0)
            AND (((flags_r & 0x400000000000) = 0) or (psfmagerr_r <= 0.2))
            AND (((flags_r & 0x100000000000) = 0) or (flags_r & 0x1000) = 0)
        """
        result = parse(sql)
        self.assertEqual(
            result,
            {
                "from": "Star",
                "select": [
                    {"value": "u"},
                    {"value": "g"},
                    {"value": "r"},
                    {"value": "i"},
                    {"value": "z"},
                    {"value": "ra"},
                    {"value": "dec"},
                    {"value": "flags_r"},
                ],
                "top": 10,
                "where": {
                    "args": [
                        {"args": ["ra", 180, 181], "op": "between"},
                        {"args": ["dec", -0.5, 0.5], "op": "between"},
                        {"args": [{"args": ["flags_r", {"hex": "10000000"}], "op": "binary_and"}, 0], "op": "neq"},
                        {"args": [{"args": ["flags_r", {"hex": "8100000c00a4"}], "op": "binary_and"}, 0], "op": "eq",},
                        {
                            "args": [
                                {
                                    "args": [{"args": ["flags_r", {"hex": "400000000000"}], "op": "binary_and"}, 0],
                                    "op": "eq",
                                },
                                {"args": ["psfmagerr_r", 0.2], "op": "lte"},
                            ],
                            "op": "or",
                        },
                        {
                            "args": [
                                {
                                    "args": [{"args": ["flags_r", {"hex": "100000000000"}], "op": "binary_and"}, 0],
                                    "op": "eq",
                                },
                                {"args": [{"args": ["flags_r", {"hex": "1000"}], "op": "binary_and"}, 0], "op": "eq",},
                            ],
                            "op": "or",
                        },
                    ],
                    "op": "and",
                },
            },
        )

    def test_issue_156b_SDSS_add_mulitply(self):
        sql = """        
            SELECT TOP 10 fld.run,
            fld.avg_sky_muJy,
            fld.runarea AS area,
            ISNULL(fp.nfirstmatch, 0)
            FROM
            (SELECT run,
            sum(primaryArea) AS runarea,
            3631e6*avg(power(cast(10 AS float), -0.4*sky_r)) AS avg_sky_muJy
            FROM Field
            GROUP BY run) AS fld
            LEFT OUTER JOIN
            (SELECT p.run,
            count(*) AS nfirstmatch
            FROM FIRST AS fm
            INNER JOIN photoprimary AS p ON p.objid=fm.objid
            GROUP BY p.run) AS fp ON fld.run=fp.run
            ORDER BY fld.run
        """
        result = parse(sql)
        self.assertEqual(
            result,
            {
                "from": [
                    {
                        "name": "fld",
                        "value": {
                            "from": "Field",
                            "groupby": {"value": "run"},
                            "select": [
                                {"value": "run"},
                                {"name": "runarea", "value": {"args": ["primaryArea"], "op": "sum"}},
                                {
                                    "name": "avg_sky_muJy",
                                    "value": {
                                        "args": [
                                            3631000000,
                                            {
                                                "args": [{
                                                    "args": [
                                                        {"args": [10, {"op": "float"}], "op": "cast"},
                                                        {"args": [-0.4, "sky_r"], "op": "mul"},
                                                    ],
                                                    "op": "power",
                                                }],
                                                "op": "avg",
                                            },
                                        ],
                                        "op": "mul",
                                    },
                                },
                            ],
                        },
                    },
                    {
                        "left outer join": {
                            "name": "fp",
                            "value": {
                                "from": [
                                    {"name": "fm", "value": "FIRST"},
                                    {
                                        "inner join": {"name": "p", "value": "photoprimary"},
                                        "on": {"args": ["p.objid", "fm.objid"], "op": "eq"},
                                    },
                                ],
                                "groupby": {"value": "p.run"},
                                "select": [
                                    {"value": "p.run"},
                                    {"name": "nfirstmatch", "value": {"args": ["*"], "op": "count"}},
                                ],
                            },
                        },
                        "on": {"args": ["fld.run", "fp.run"], "op": "eq"},
                    },
                ],
                "orderby": {"value": "fld.run"},
                "select": [
                    {"value": "fld.run"},
                    {"value": "fld.avg_sky_muJy"},
                    {"name": "area", "value": "fld.runarea"},
                    {"value": {"args": ["fp.nfirstmatch", 0], "op": "isnull"}},
                ],
                "top": 10,
            },
        )

    def test_issue_156b_SDSS(self):
        sql = """        
            SELECT TOP 10 fld.run,
            fld.avg_sky_muJy,
            fld.runarea AS area,
            ISNULL(fp.nfirstmatch, 0)
            FROM
            (SELECT run,
            sum(primaryArea) AS runarea,
            3631e6avg(power(cast(10. AS float), -0.4sky_r)) AS avg_sky_muJy
            FROM Field
            GROUP BY run) AS fld
            LEFT OUTER JOIN
            (SELECT p.run,
            count(*) AS nfirstmatch
            FROM FIRST AS fm
            INNER JOIN photoprimary AS p ON p.objid=fm.objid
            GROUP BY p.run) AS fp ON fld.run=fp.run
            ORDER BY fld.run
        """
        result = parse(sql)
        self.assertEqual(
            result,
            {
                "from": [
                    {
                        "name": "fld",
                        "value": {
                            "from": "Field",
                            "groupby": {"value": "run"},
                            "select": [
                                {"value": "run"},
                                {"name": "runarea", "value": {"args": ["primaryArea"], "op": "sum"}},
                                {
                                    "name": "avg_sky_muJy",
                                    "value": {"mul": [
                                        3631000000,
                                        {
                                            "args": [{
                                                "args": [
                                                    {"args": [10.0, {"op": "float"}], "op": "cast"},
                                                    {"args": [{"mul": [0.4, "sky_r"]}], "op": "neg"},
                                                ],
                                                "op": "power",
                                            }],
                                            "op": "avg",
                                        },
                                    ]},
                                },
                            ],
                        },
                    },
                    {
                        "left outer join": {
                            "name": "fp",
                            "value": {
                                "from": [
                                    {"name": "fm", "value": "FIRST"},
                                    {
                                        "inner join": {"name": "p", "value": "photoprimary"},
                                        "on": {"args": ["p.objid", "fm.objid"], "op": "eq"},
                                    },
                                ],
                                "groupby": {"value": "p.run"},
                                "select": [
                                    {"value": "p.run"},
                                    {"name": "nfirstmatch", "value": {"args": ["*"], "op": "count"}},
                                ],
                            },
                        },
                        "on": {"args": ["fld.run", "fp.run"], "op": "eq"},
                    },
                ],
                "orderby": {"value": "fld.run"},
                "select": [
                    {"value": "fld.run"},
                    {"value": "fld.avg_sky_muJy"},
                    {"name": "area", "value": "fld.runarea"},
                    {"value": {"args": ["fp.nfirstmatch", 0], "op": "isnull"}},
                ],
                "top": 10,
            },
        )

    def test_minus(self):
        sql = """select name from employee
        minus
        select 'Alan' from dual
        """
        result = parse(sql)
        expected = {"minus": [
            {"from": "employee", "select": {"value": "name"}},
            {"from": "dual", "select": {"value": {"literal": "Alan"}}},
        ]}
        self.assertEqual(result, expected)

    def test_issue_32_not_ascii(self):
        sql = """select äce from motorhead"""
        result = parse(sql)
        expected = {"from": "motorhead", "select": {"value": "äce"}}
        self.assertEqual(result, expected)

    def test_issue_89_negative_numbers(self):
        sql = """SELECT * FROM dbo.a where ABS(a) * -1 = -22"""
        result = parse(sql)
        expected = {
            "from": "dbo.a",
            "select": "*",
            "where": {"op": "eq", "args": [{"op": "mul", "args": [{"args": ["a"], "op": "abs"}, -1]}, -22]},
        }
        self.assertEqual(result, expected)
