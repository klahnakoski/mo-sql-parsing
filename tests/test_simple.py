# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from unittest import TestCase

from mo_sql_parsing import parse, parse_mysql, format, SQL_NULL, simple_op, normal_op

try:
    from tests.util import assertRaises
except ImportError:
    from .util import assertRaises  # RELATIVE IMPORT SO WE CAN RUN IN pyLibrary


class TestSimple(TestCase):

    # @classmethod
    # def setUpClass(cls):
    #     from mo_parsing.profile import Profiler
    #     cls.profiler = Profiler("test_simple")
    #     cls.profiler.__enter__()
    #
    # @classmethod
    # def tearDownClass(cls):
    #     cls.profiler.__exit__(None, None, None)

    def test_two_tables(self):
        result = parse("SELECT * from XYZZY, ABC")
        expected = {"select": "*", "from": ["XYZZY", "ABC"]}
        self.assertEqual(result, expected)

    def test_dot_table_name(self):
        result = parse("select * from SYS.XYZZY")
        expected = {"select": "*", "from": "SYS.XYZZY"}
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
            "select": {"value": {"add": ["a", {"div": ["b", 2]}, {"mul": [45, "c"]}, {"div": [2, "d"]}]}},
            "from": "dual",
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
            "select": "*",
            "from": "dual",
            "where": {"neq": ["a", {"literal": "test"}]},
        }
        self.assertEqual(result, expected)

    def test_where_in(self):
        result = parse("SELECT a FROM dual WHERE a in ('r', 'g', 'b')")
        expected = {
            "select": {"value": "a"},
            "from": "dual",
            "where": {"in": ["a", {"literal": ["r", "g", "b"]}]},
        }
        self.assertEqual(result, expected)

    def test_where_in_and_in(self):
        #                         1         2         3         4         5         6
        #               0123456789012345678901234567890123456789012345678901234567890123456789
        result = parse("SELECT a FROM dual WHERE a in ('r', 'g', 'b') AND b in (10, 11, 12)")
        expected = {
            "select": {"value": "a"},
            "from": "dual",
            "where": {"and": [{"in": ["a", {"literal": ["r", "g", "b"]}]}, {"in": ["b", [10, 11, 12]]}]},
        }
        self.assertEqual(result, expected)

    def test_eq(self):
        result = parse("SELECT a, b FROM t1, t2 WHERE t1.a=t2.b")
        expected = {
            "select": [{"value": "a"}, {"value": "b"}],
            "from": ["t1", "t2"],
            "where": {"eq": ["t1.a", "t2.b"]},
        }
        self.assertEqual(result, expected)

    def test_is_null(self):
        result = parse("SELECT a, b FROM t1 WHERE t1.a IS NULL")
        expected = {
            "select": [{"value": "a"}, {"value": "b"}],
            "from": "t1",
            "where": {"missing": "t1.a"},
        }
        self.assertEqual(result, expected)

    def test_is_not_null(self):
        result = parse("SELECT a, b FROM t1 WHERE t1.a IS NOT NULL")
        expected = {
            "select": [{"value": "a"}, {"value": "b"}],
            "from": "t1",
            "where": {"exists": "t1.a"},
        }
        self.assertEqual(result, expected)

    def test_groupby(self):
        result = parse("select a, count(1) as b from mytable group by a")
        expected = {
            "select": [{"value": "a"}, {"name": "b", "value": {"count": 1}}],
            "from": "mytable",
            "groupby": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_function(self):
        #               0         1         2
        #               0123456789012345678901234567890
        result = parse("select count(1) from mytable")
        expected = {"select": {"value": {"count": 1}}, "from": "mytable"}
        self.assertEqual(result, expected)

    def test_function_underscore(self):
        #               0         1         2
        #               0123456789012345678901234567890
        result = parse("select DATE_TRUNC('2019-04-12', WEEK) from mytable")
        expected = {
            "select": {"value": {"date_trunc": [{"literal": "2019-04-12"}, "WEEK"]}},
            "from": "mytable",
        }
        self.assertEqual(result, expected)

    def test_order_by(self):
        result = parse("select count(1) from dual order by a")
        expected = {
            "select": {"value": {"count": 1}},
            "from": "dual",
            "orderby": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_order_by_asc(self):
        result = parse("select count(1) from dual order by a asc")
        expected = {
            "select": {"value": {"count": 1}},
            "from": "dual",
            "orderby": {"value": "a", "sort": "asc"},
        }
        self.assertEqual(result, expected)

    def test_neg_or_precedence(self):
        result = parse("select B,C from table1 where A=-900 or B=100")
        expected = {
            "from": "table1",
            "where": {"or": [{"eq": ["A", -900]}, {"eq": ["B", 100]}]},
            "select": [{"value": "B"}, {"value": "C"}],
        }
        self.assertEqual(result, expected)

    def test_negative_number(self):
        result = parse("select a from table1 where A=-900")
        expected = {
            "from": "table1",
            "where": {"eq": ["A", -900]},
            "select": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_like_in_where(self):
        result = parse("select a from table1 where A like '%20%'")
        expected = {
            "from": "table1",
            "where": {"like": ["A", {"literal": "%20%"}]},
            "select": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_not_like_in_where(self):
        result = parse("select a from table1 where A not like '%20%'")
        expected = {
            "from": "table1",
            "where": {"not_like": ["A", {"literal": "%20%"}]},
            "select": {"value": "a"},
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
                "value": {"case": [{"when": {"like": ["A", {"literal": "bb%"}]}, "then": 1}, 0]},
            },
        }
        self.assertEqual(result, expected)

    def test_switch_else(self):
        result = parse("select case table0.y1 when 'a' then 1 else 0 end from table0")
        expected = {
            "select": {"value": {"case": [{"when": {"eq": ["table0.y1", {"literal": "a"}]}, "then": 1}, 0]}},
            "from": "table0",
        }
        self.assertEqual(result, expected)

    def test_not_like_in_select(self):
        result = parse("select case when A not like 'bb%' then 1 else 0 end as bb from table1")
        expected = {
            "from": "table1",
            "select": {
                "name": "bb",
                "value": {"case": [{"when": {"not_like": ["A", {"literal": "bb%"}]}, "then": 1}, 0]},
            },
        }
        self.assertEqual(result, expected)

    def test_like_from_pr16(self):
        result = parse("select * from trade where school LIKE '%shool' and name='abc' and id IN ('1','2')")
        expected = {
            "from": "trade",
            "where": {"and": [
                {"like": ["school", {"literal": "%shool"}]},
                {"eq": ["name", {"literal": "abc"}]},
                {"in": ["id", {"literal": ["1", "2"]}]},
            ]},
            "select": "*",
        }
        self.assertEqual(result, expected)

    def test_rlike_in_where(self):
        result = parse("select a from table1 where A rlike '.*20.*'")
        expected = {
            "from": "table1",
            "where": {"rlike": ["A", {"literal": ".*20.*"}]},
            "select": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_not_rlike_in_where(self):
        result = parse("select a from table1 where A not rlike '.*20.*'")
        expected = {
            "from": "table1",
            "where": {"not_rlike": ["A", {"literal": ".*20.*"}]},
            "select": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_rlike_in_select(self):
        result = parse("select case when A rlike 'bb.*' then 1 else 0 end as bb from table1")
        expected = {
            "from": "table1",
            "select": {
                "name": "bb",
                "value": {"case": [{"when": {"rlike": ["A", {"literal": "bb.*"}]}, "then": 1}, 0]},
            },
        }
        self.assertEqual(result, expected)

    def test_not_rlike_in_select(self):
        result = parse("select case when A not rlike 'bb.*' then 1 else 0 end as bb from table1")
        expected = {
            "from": "table1",
            "select": {
                "name": "bb",
                "value": {"case": [{"when": {"not_rlike": ["A", {"literal": "bb.*"}]}, "then": 1}, 0]},
            },
        }
        self.assertEqual(result, expected)

    def test_in_expression(self):
        result = parse("select * from task where repo.branch.name in ('try', 'mozilla-central')")
        expected = {
            "from": "task",
            "select": "*",
            "where": {"in": ["repo.branch.name", {"literal": ["try", "mozilla-central"]}]},
        }
        self.assertEqual(result, expected)

    def test_not_in_expression(self):
        result = parse("select * from task where repo.branch.name not in ('try', 'mozilla-central')")
        expected = {
            "from": "task",
            "select": "*",
            "where": {"nin": ["repo.branch.name", {"literal": ["try", "mozilla-central"]}]},
        }
        self.assertEqual(result, expected)

    def test_joined_table_name(self):
        result = parse("SELECT * FROM table1 t1 JOIN table3 t3 ON t1.id = t3.id")

        expected = {
            "from": [
                {"name": "t1", "value": "table1"},
                {"on": {"eq": ["t1.id", "t3.id"]}, "join": {"name": "t3", "value": "table3"}},
            ],
            "select": "*",
        }
        self.assertEqual(result, expected)

    def test_not_equal(self):
        #               0         1         2         3         4         5         6        7          8
        #               012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        result = parse("select * from task where build.product is not null and build.product!='firefox'")

        expected = {
            "select": "*",
            "from": "task",
            "where": {"and": [{"exists": "build.product"}, {"neq": ["build.product", {"literal": "firefox"}]}]},
        }
        self.assertEqual(result, expected)

    def test_pr19(self):
        result = parse("select empid from emp where ename like 's%' ")
        expected = {
            "from": "emp",
            "where": {"like": ["ename", {"literal": "s%"}]},
            "select": {"value": "empid"},
        }
        self.assertEqual(result, expected)

    def test_backtick(self):
        result = parse("SELECT `user ID` FROM a")
        expected = {"select": {"value": "user ID"}, "from": "a"}
        self.assertEqual(result, expected)

    def test_backtick_escape(self):
        result = parse("SELECT `user`` ID` FROM a")
        expected = {"select": {"value": "user` ID"}, "from": "a"}
        self.assertEqual(result, expected)

    def test_left_join(self):
        result = parse("SELECT t1.field1 FROM t1 LEFT JOIN t2 ON t1.id = t2.id")
        expected = {
            "select": {"value": "t1.field1"},
            "from": ["t1", {"left join": "t2", "on": {"eq": ["t1.id", "t2.id"]}}],
        }
        self.assertEqual(result, expected)

    def test_multiple_left_join(self):
        result = parse("SELECT t1.field1 FROM t1 LEFT JOIN t2 ON t1.id = t2.id LEFT JOIN t3 ON t1.id = t3.id")
        expected = {
            "select": {"value": "t1.field1"},
            "from": [
                "t1",
                {"left join": "t2", "on": {"eq": ["t1.id", "t2.id"]}},
                {"left join": "t3", "on": {"eq": ["t1.id", "t3.id"]}},
            ],
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
            "select": {"value": "t1.field1"},
            "from": ["t1", {"left outer join": "t2", "on": {"eq": ["t1.id", "t2.id"]}}],
        }
        self.assertEqual(result, expected)

    def test_right_join(self):
        result = parse("SELECT t1.field1 FROM t1 RIGHT JOIN t2 ON t1.id = t2.id")
        expected = {
            "select": {"value": "t1.field1"},
            "from": ["t1", {"right join": "t2", "on": {"eq": ["t1.id", "t2.id"]}}],
        }
        self.assertEqual(result, expected)

    def test_right_outer_join(self):
        result = parse("SELECT t1.field1 FROM t1 RIGHT OUTER JOIN t2 ON t1.id = t2.id")
        expected = {
            "select": {"value": "t1.field1"},
            "from": ["t1", {"right outer join": "t2", "on": {"eq": ["t1.id", "t2.id"]}}],
        }
        self.assertEqual(result, expected)

    def test_full_join(self):
        result = parse("SELECT t1.field1 FROM t1 FULL JOIN t2 ON t1.id = t2.id")
        expected = {
            "select": {"value": "t1.field1"},
            "from": ["t1", {"full join": "t2", "on": {"eq": ["t1.id", "t2.id"]}}],
        }
        self.assertEqual(result, expected)

    def test_full_outer_join(self):
        result = parse("SELECT t1.field1 FROM t1 FULL OUTER JOIN t2 ON t1.id = t2.id")
        expected = {
            "select": {"value": "t1.field1"},
            "from": ["t1", {"full outer join": "t2", "on": {"eq": ["t1.id", "t2.id"]}}],
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
            "select": {"value": "a"},
            "from": "dual",
            "where": {"between": ["a", 1, 2]},
        }
        self.assertEqual(result, expected)

    def test_where_not_between(self):
        result = parse("SELECT a FROM dual WHERE a NOT BETWEEN 1 and 2")
        expected = {
            "select": {"value": "a"},
            "from": "dual",
            "where": {"not_between": ["a", 1, 2]},
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
            "select": {"value": {"deflate": {"sum": {"int": "mobile_price.price"}}}},
            "from": "mobile",
        }
        self.assertEqual(result, expected)

    def test_issue_90(self):
        result = parse(
            """SELECT MIN(cn.name) AS from_company
        FROM company_name AS cn, company_type AS ct, keyword AS k, movie_link AS ml, title AS t
        WHERE cn.country_code !='[pl]' AND ct.kind IS NOT NULL AND t.production_year > 1950 AND ml.movie_id = t.id
        """
        )

        expected = {
            "select": {"value": {"min": "cn.name"}, "name": "from_company"},
            "from": [
                {"value": "company_name", "name": "cn"},
                {"value": "company_type", "name": "ct"},
                {"value": "keyword", "name": "k"},
                {"value": "movie_link", "name": "ml"},
                {"value": "title", "name": "t"},
            ],
            "where": {"and": [
                {"neq": ["cn.country_code", {"literal": "[pl]"}]},
                {"exists": "ct.kind"},
                {"gt": ["t.production_year", 1950]},
                {"eq": ["ml.movie_id", "t.id"]},
            ]},
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
            "where": {"and": [
                {"exists": "an.name"},
                {"or": [{"like": ["an.name", {"literal": "%a%"}]}, {"like": ["an.name", {"literal": "A%"}]}]},
                {"eq": ["it.info", {"literal": "mini biography"}]},
                {"in": ["lt.link", {"literal": ["references", "referenced in", "features", "featured in"]}]},
                {"between": ["n.name_pcode_cf", {"literal": "A"}, {"literal": "F"}]},
                {"or": [
                    {"eq": ["n.gender", {"literal": "m"}]},
                    {"and": [{"eq": ["n.gender", {"literal": "f"}]}, {"like": ["n.name", {"literal": "A%"}]}]},
                ]},
                {"exists": "pi.note"},
                {"between": ["t.production_year", 1980, 2010]},
                {"eq": ["n.id", "an.person_id"]},
                {"eq": ["n.id", "pi.person_id"]},
                {"eq": ["ci.person_id", "n.id"]},
                {"eq": ["t.id", "ci.movie_id"]},
                {"eq": ["ml.linked_movie_id", "t.id"]},
                {"eq": ["lt.id", "ml.link_type_id"]},
                {"eq": ["it.id", "pi.info_type_id"]},
                {"eq": ["pi.person_id", "an.person_id"]},
                {"eq": ["pi.person_id", "ci.person_id"]},
                {"eq": ["an.person_id", "ci.person_id"]},
                {"eq": ["ci.movie_id", "ml.linked_movie_id"]},
            ]},
        }
        self.assertEqual(result, expected)

    def test_issue_68b(self):
        #      0         1         2         3         4         5         6         7         8         9
        #      012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        sql = "SELECT COUNT(*) AS CNT FROM test.tb WHERE (id IN (unhex('1'),unhex('2'))) AND  status=1;"
        result = parse(sql)
        expected = {
            "select": {"value": {"count": "*"}, "name": "CNT"},
            "from": "test.tb",
            "where": {"and": [
                {"in": ["id", [{"unhex": {"literal": "1"}}, {"unhex": {"literal": "2"}}]]},
                {"eq": ["status", 1]},
            ]},
        }
        self.assertEqual(result, expected)

    def test_binary_and(self):
        sql = "SELECT * FROM t WHERE  c & 4;"
        result = parse(sql)
        expected = {"select": "*", "from": "t", "where": {"binary_and": ["c", 4]}}
        self.assertEqual(result, expected)

    def test_binary_or(self):
        sql = "SELECT * FROM t WHERE c | 4;"
        result = parse(sql)
        expected = {"select": "*", "from": "t", "where": {"binary_or": ["c", 4]}}
        self.assertEqual(result, expected)

    def test_binary_not(self):
        #      0         1         2
        #      012345678901234567890123456789
        sql = "SELECT * FROM t WHERE ~c;"
        result = parse(sql)
        expected = {"select": "*", "from": "t", "where": {"binary_not": "c"}}
        self.assertEqual(result, expected)

    def test_or_and(self):
        sql = "SELECT * FROM dual WHERE a OR b AND c"
        result = parse(sql)
        expected = {
            "select": "*",
            "from": "dual",
            "where": {"or": ["a", {"and": ["b", "c"]}]},
        }
        self.assertEqual(result, expected)

    def test_and_or(self):
        sql = "SELECT * FROM dual WHERE a AND b or c"
        result = parse(sql)
        expected = {
            "select": "*",
            "from": "dual",
            "where": {"or": [{"and": ["a", "b"]}, "c"]},
        }
        self.assertEqual(result, expected)

    def test_underscore_function1(self):
        sql = "SELECT _()"
        result = parse(sql)
        expected = {
            "select": {"value": {"_": {}}},
        }
        self.assertEqual(result, expected)

    def test_underscore_function2(self):
        sql = "SELECT _a(a$b)"
        result = parse(sql)
        expected = {
            "select": {"value": {"_a": "a$b"}},
        }
        self.assertEqual(result, expected)

    def test_underscore_function3(self):
        sql = "SELECT _$$_(a, b$)"
        result = parse(sql)
        expected = {
            "select": {"value": {"_$$_": ["a", "b$"]}},
        }
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
            "select": "*",
            "from": "MyTable",
            "groupby": {"value": "Col"},
            "having": {"or": [
                {"and": [{"gte": [{"avg": "X"}, 2]}, {"lte": [{"avg": "X"}, 4]}]},
                {"eq": [{"avg": "X"}, 5]},
            ]},
        }
        self.assertEqual(result, expected)

    def test_issue97_function_names(self):
        sql = "SELECT ST_AsText(ST_MakePoint(174, -36));"
        result = parse(sql)
        expected = {"select": {"value": {"st_astext": {"st_makepoint": [174, -36]}}}}
        self.assertEqual(result, expected)

    def test_issue91_order_of_operations1(self):
        sql = "select 5-4+2"
        result = parse(sql)
        expected = {"select": {"value": {"add": [{"sub": [5, 4]}, 2]}}}
        self.assertEqual(result, expected)

    def test_issue91_order_of_operations2(self):
        sql = "select 5/4*2"
        result = parse(sql)
        expected = {"select": {"value": {"mul": [{"div": [5, 4]}, 2]}}}
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
            "with": {
                "name": "dept_count",
                "value": {
                    "from": "emp",
                    "groupby": {"value": "deptno"},
                    "select": [{"value": "deptno"}, {"name": "dept_count", "value": {"count": "*"}}],
                },
            },
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
            "where": {"and": [
                {"eq": ["e.deptno", "dc1.deptno"]},
                {"eq": ["e.mgr", "m.empno"]},
                {"eq": ["m.deptno", "dc2.deptno"]},
            ]},
        }

        self.assertEqual(result, expected)

    def test_2with_clause(self):
        #    0         1         2         3         4         5         6         7         8         9
        #    012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        sql = " WITH a AS (SELECT 1), b AS (SELECT 2) SELECT * FROM a UNION ALL SELECT * FROM b"
        result = parse(sql)
        expected = {
            "with": [
                {"name": "a", "value": {"select": {"value": 1}}},
                {"name": "b", "value": {"select": {"value": 2}}},
            ],
            "union_all": [{"select": "*", "from": "a"}, {"select": "*", "from": "b"}],
        }
        self.assertEqual(result, expected)

    def test_issue_38a(self):
        sql = "SELECT a IN ('abc',3,'def')"
        result = parse(sql)
        expected = {"select": {"value": {"in": ["a", {"literal": ["abc", 3, "def"]}]}}}
        self.assertEqual(result, expected)

    def test_issue_38b(self):
        sql = "SELECT a IN (abc,3,'def')"
        result = parse(sql)
        expected = {"select": {"value": {"in": ["a", ["abc", 3, {"literal": "def"}]]}}}
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
            "where": {"eq": [
                "population",
                {
                    "from": "city",
                    "select": {"value": {"max": "population"}},
                    "where": {"in": [
                        "state_name",
                        {
                            "from": "state",
                            "select": {"value": "state_name"},
                            "where": {"eq": ["area", {"from": "state", "select": {"value": {"min": "area"}}}]},
                        },
                    ]},
                },
            ]},
        }
        self.assertEqual(result, expected)

    def test_issue_95(self):
        #      0         1         2         3         4         5         6         7         8         9
        #      012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        sql = "select * from some_table.some_function('parameter', 1, some_col)"
        result = parse(sql)
        expected = {
            "select": "*",
            "from": {"some_table.some_function": [{"literal": "parameter"}, 1, "some_col"]},
        }
        self.assertEqual(result, expected)

    def test_at_ident(self):
        sql = "select @@version_comment"
        result = parse(sql)
        expected = {"select": {"value": "@@version_comment"}}
        self.assertEqual(result, expected)

    def test_date(self):
        sql = "select DATE '2020 01 25'"
        result = parse(sql)
        expected = {"select": {"value": {"date": {"literal": "2020 01 25"}}}}
        self.assertEqual(result, expected)

    def test_interval(self):
        sql = "select INTErval 30.5 monthS"
        result = parse(sql)
        expected = {"select": {"value": {"interval": [30.5, "month"]}}}
        self.assertEqual(result, expected)

    def test_date_less_interval(self):
        sql = "select DATE '2020 01 25' - interval 4 seconds"
        result = parse(sql)
        expected = {"select": {"value": {"sub": [{"date": {"literal": "2020 01 25"}}, {"interval": [4, "second"]}]}}}
        self.assertEqual(result, expected)

    def test_issue_141(self):
        sql = "select name from table order by age offset 3 limit 1"
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
            "select": {"value": {"count": "url"}},
            "from": "crawl_urls",
            "where": {"and": [
                {"eq": ["http_status_code", 200]},
                {"eq": ["meta_redirect", False]},
                {"eq": ["primary_page", True]},
                {"eq": ["indexable", True]},
                {"eq": ["canonicalized_page", False]},
                {"or": [
                    {"eq": ["paginated_page", False]},
                    {"and": [{"eq": ["paginated_page", True]}, {"eq": ["page_1", True]}]},
                ]},
                {"neq": ["css", True]},
                {"neq": ["js", True]},
                {"neq": ["is_image", True]},
                {"eq": ["internal", True]},
                {"or": [
                    {"eq": ["header_content_type", {"literal": "text/html"}]},
                    {"eq": ["header_content_type", {"literal": ""}]},
                ]},
            ]},
            "orderby": {"value": {"count": "url"}, "sort": "desc"},
        }
        self.assertEqual(result, expected)

    def test_and_w_tuple(self):
        #      0         1         2         3         4         5         6         7         8         9
        #      012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        sql = "SELECT * FROM a WHERE ((a = 1 AND (b=2 AND c=3, False)))"
        result = parse(sql)
        expected = {
            "select": "*",
            "from": "a",
            "where": {"and": [{"eq": ["a", 1]}, [{"and": [{"eq": ["b", 2]}, {"eq": ["c", 3]}]}, False]]},
        }
        self.assertEqual(result, expected)

    def test_and_w_tuple2(self):
        sql = "SELECT ('a', 'b', 'c')"
        result = parse(sql)
        expected = {
            "select": {"value": {"literal": ["a", "b", "c"]}},
        }
        self.assertEqual(result, expected)

    def test_null_parameter(self):
        sql = "select DECODE(A, NULL, 'b')"
        result = parse(sql)
        expected = {"select": {"value": {"decode": ["A", {"null": {}}, {"literal": "b"}]}}}
        self.assertEqual(result, expected)

    def test_issue140(self):
        sql = "select rank(*) over (partition by a order by b, c) from tab"
        result = parse(sql)
        expected = {
            "select": {
                "value": {"rank": "*"},
                "over": {"partitionby": "a", "orderby": [{"value": "b"}, {"value": "c"}]},
            },
            "from": "tab",
        }
        self.assertEqual(result, expected)

    def test_issue119(self):
        sql = "SELECT 1 + CAST(1 AS INT) result"
        result = parse(sql)
        expected = {"select": {"value": {"add": [1, {"cast": [1, {"int": {}}]}]}, "name": "result"}}
        self.assertEqual(result, expected)

    def test_issue120(self):
        sql = "SELECT DISTINCT Country, City FROM Customers"
        result = parse(sql)
        expected = {
            "select_distinct": [{"value": "Country"}, {"value": "City"}],
            "from": "Customers",
        }
        self.assertEqual(result, expected)

    def test_issue1_of_fork(self):
        #      0         1         2
        #      012345678901234567890123456789
        sql = "SELECT * FROM jobs LIMIT 10"
        result = parse(sql)
        self.assertEqual(result, {"select": "*", "from": "jobs", "limit": 10})

    def test_issue2a_of_fork(self):
        sql = "SELECT COUNT(DISTINCT Y) FROM A "
        result = parse(sql)
        self.assertEqual(
            result, {"from": "A", "select": {"value": {"count": "Y", "distinct": True}}},
        )

    def test_issue2b_of_fork(self):
        sql = "SELECT COUNT( DISTINCT B, E), A FROM C WHERE D= X GROUP BY A"
        result = parse(sql)
        self.assertEqual(
            result,
            {
                "from": "C",
                "select": [{"value": {"count": ["B", "E"], "distinct": True}}, {"value": "A"}],
                "where": {"eq": ["D", "X"]},
                "groupby": {"value": "A"},
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
                    "value": {"rank": "*"},
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
                "from": "Star",
                "where": {"and": [
                    {"between": ["ra", 180, 181]},
                    {"between": ["dec", -0.5, 0.5]},
                    {"neq": [{"binary_and": ["flags_r", {"hex": "10000000"}]}, 0]},
                    {"eq": [{"binary_and": ["flags_r", {"hex": "8100000c00a4"}]}, 0]},
                    {"or": [
                        {"eq": [{"binary_and": ["flags_r", {"hex": "400000000000"}]}, 0]},
                        {"lte": ["psfmagerr_r", 0.2]},
                    ]},
                    {"or": [
                        {"eq": [{"binary_and": ["flags_r", {"hex": "100000000000"}]}, 0]},
                        {"eq": [{"binary_and": ["flags_r", {"hex": "1000"}]}, 0]},
                    ]},
                ]},
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
                "select": [
                    {"value": "fld.run"},
                    {"value": "fld.avg_sky_muJy"},
                    {"name": "area", "value": "fld.runarea"},
                    {"value": {"isnull": ["fp.nfirstmatch", 0]}},
                ],
                "top": 10,
                "from": [
                    {
                        "name": "fld",
                        "value": {
                            "select": [
                                {"value": "run"},
                                {"name": "runarea", "value": {"sum": "primaryArea"}},
                                {
                                    "name": "avg_sky_muJy",
                                    "value": {"mul": [
                                        3631000000,
                                        {"avg": {"power": [{"cast": [10, {"float": {}}]}, {"mul": [-0.4, "sky_r"]}]}},
                                    ]},
                                },
                            ],
                            "from": "Field",
                            "groupby": {"value": "run"},
                        },
                    },
                    {
                        "left outer join": {
                            "name": "fp",
                            "value": {
                                "select": [{"value": "p.run"}, {"name": "nfirstmatch", "value": {"count": "*"}}],
                                "from": [
                                    {"name": "fm", "value": "FIRST"},
                                    {
                                        "inner join": {"name": "p", "value": "photoprimary"},
                                        "on": {"eq": ["p.objid", "fm.objid"]},
                                    },
                                ],
                                "groupby": {"value": "p.run"},
                            },
                        },
                        "on": {"eq": ["fld.run", "fp.run"]},
                    },
                ],
                "orderby": {"value": "fld.run"},
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
                "select": [
                    {"value": "fld.run"},
                    {"value": "fld.avg_sky_muJy"},
                    {"name": "area", "value": "fld.runarea"},
                    {"value": {"isnull": ["fp.nfirstmatch", 0]}},
                ],
                "top": 10,
                "from": [
                    {
                        "name": "fld",
                        "value": {
                            "select": [
                                {"value": "run"},
                                {"name": "runarea", "value": {"sum": "primaryArea"}},
                                {
                                    "name": "avg_sky_muJy",
                                    "value": {"mul": [
                                        3631000000,
                                        {"avg": {"power": [
                                            {"cast": [10.0, {"float": {}}]},
                                            {"neg": {"mul": [0.4, "sky_r"]}},
                                        ]}},
                                    ]},
                                },
                            ],
                            "from": "Field",
                            "groupby": {"value": "run"},
                        },
                    },
                    {
                        "left outer join": {
                            "name": "fp",
                            "value": {
                                "select": [{"value": "p.run"}, {"name": "nfirstmatch", "value": {"count": "*"}}],
                                "from": [
                                    {"name": "fm", "value": "FIRST"},
                                    {
                                        "inner join": {"name": "p", "value": "photoprimary"},
                                        "on": {"eq": ["p.objid", "fm.objid"]},
                                    },
                                ],
                                "groupby": {"value": "p.run"},
                            },
                        },
                        "on": {"eq": ["fld.run", "fp.run"]},
                    },
                ],
                "orderby": {"value": "fld.run"},
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

    def test_issue_20b_intersect(self):
        sql = "SELECT login_name FROM Course_Authors_and_Tutors INTERSECT SELECT login_name FROM Students"
        result = parse(sql)
        expected = {"intersect": [
            {"from": "Course_Authors_and_Tutors", "select": {"value": "login_name"}},
            {"from": "Students", "select": {"value": "login_name"}},
        ]}
        self.assertEqual(result, expected)

    def test_values_w_union(self):
        sql = "values (1, 2, 3) union all select * from A"
        result = parse(sql)
        expected = {"union_all": [
            {"select": [{"value": 1}, {"value": 2}, {"value": 3}]},
            {"select": "*", "from": "A"},
        ]}
        self.assertEqual(result, expected)

    def test_issue_49(self):
        # bad spelling of distinct
        q = "select DISTICT col_a, col_b from table_test"
        parsed_query = parse_mysql(q)
        self.assertEqual(
            parsed_query,
            {"select": [{"value": "DISTICT", "name": "col_a"}, {"value": "col_b"}], "from": "table_test"},
        )

    def test_issue_67_trim1(self):
        sql = "SELECT TRIM(BOTH FROM column1) FROM my_table"
        p = parse(sql)
        s = format(p)
        self.assertEqual(
            p, {"from": "my_table", "select": {"value": {"direction": "both", "trim": "column1"}}},
        )
        self.assertEqual(s, "SELECT TRIM(BOTH FROM column1) FROM my_table")

    def test_issue_67_trim2(self):
        sql = "SELECT TRIM(TRAILING FROM column1) FROM my_table"
        p = parse(sql)
        s = format(p)
        self.assertEqual(
            p, {"from": "my_table", "select": {"value": {"direction": "trailing", "trim": "column1"}}},
        )
        self.assertEqual(s, "SELECT TRIM(TRAILING FROM column1) FROM my_table")

    def test_issue_67_trim3(self):
        sql = "SELECT TRIM(LEADING FROM column1) FROM my_table"
        p = parse(sql)
        s = format(p)
        self.assertEqual(
            p, {"from": "my_table", "select": {"value": {"direction": "leading", "trim": "column1"}}},
        )
        self.assertEqual(s, "SELECT TRIM(LEADING FROM column1) FROM my_table")

    def test_issue_67_trim4(self):
        sql = "SELECT TRIM(TRAILING '.1' from column1) FROM my_table"
        p = parse(sql)
        s = format(p)
        self.assertEqual(
            p,
            {
                "from": "my_table",
                "select": {"value": {"direction": "trailing", "characters": {"literal": ".1"}, "trim": "column1"}},
            },
        )
        self.assertEqual(s, "SELECT TRIM(TRAILING '.1' FROM column1) FROM my_table")

    def test_issue_67_trim5(self):
        sql = "SELECT TRIM(LEADING '.1' from column1) FROM my_table"
        p = parse(sql)
        s = format(p)
        self.assertEqual(
            p,
            {
                "from": "my_table",
                "select": {"value": {"direction": "leading", "characters": {"literal": ".1"}, "trim": "column1"}},
            },
        )
        self.assertEqual(s, "SELECT TRIM(LEADING '.1' FROM column1) FROM my_table")

    def test_issue_67_trim6(self):
        sql = "SELECT TRIM(BOTH '.1' from column1) FROM my_table"
        p = parse(sql)
        s = format(p)
        self.assertEqual(
            p,
            {
                "from": "my_table",
                "select": {"value": {"direction": "both", "characters": {"literal": ".1"}, "trim": "column1"}},
            },
        )
        self.assertEqual(s, "SELECT TRIM(BOTH '.1' FROM column1) FROM my_table")

    def test_issue_67_trim7(self):
        # With embedded trim function
        sql = "SELECT TRIM('.1' from TRIM(column1)) FROM my_table"
        p = parse(sql)
        s = format(p)
        self.assertEqual(
            p,
            {"from": "my_table", "select": {"value": {"characters": {"literal": ".1"}, "trim": {"trim": "column1"}}},},
        )
        self.assertEqual(s, """SELECT TRIM(\'.1\' FROM TRIM(column1)) FROM my_table""")

    def test_issue_68_group_strings(self):
        sql = """SELECT * FROM AirlineFlights WHERE (origin, dest) IN (('ATL', 'ABE'), ('DFW', 'ABI'))"""
        p = parse(sql)
        self.assertEqual(
            p,
            {
                "from": "AirlineFlights",
                "select": "*",
                "where": {"in": [["origin", "dest"], {"literal": [["ATL", "ABE"], ["DFW", "ABI"]]}]},
            },
        )

    def test_issue_70_fetch_next(self):
        # https://www.sqltutorial.org/sql-fetch/
        sql = """SELECT * FROM mytable FETCH NEXT 20 ROWS ONLY"""
        result = parse(sql)
        self.assertEqual(result, {"from": "mytable", "fetch": 20, "select": "*"})

    def test_issue_70_offset_fetch_next(self):
        # https://www.sqltutorial.org/sql-fetch/
        sql = """SELECT * FROM mytable offset 2 FETCH 10"""
        result = parse(sql)
        self.assertEqual(result, {"from": "mytable", "offset": 2, "fetch": 10, "select": "*"})

    def test_issue_75_comments(self):
        self.assertEqual(parse("/* foo */ SELECT TRUE"), {"select": {"value": True}})

        self.assertEqual(parse("SELECT /* foo */ TRUE"), {"select": {"value": True}})

        self.assertEqual(parse("SELECT TRUE /* foo */"), {"select": {"value": True}})

        self.assertEqual(parse("/* foo */\nSELECT TRUE"), {"select": {"value": True}})

        self.assertEqual(parse("/* \nfoo\n\n */\nSELECT TRUE"), {"select": {"value": True}})

    def test_issue_91_all(self):
        result = parse("select count(*) from all")
        expected = {"select": {"value": {"count": "*"}}, "from": "all"}
        self.assertEqual(result, expected)

    def test_issue_95_key_as_column_name(self):
        result = parse("SELECT key, value FROM `a.b.c`")
        expected = {"from": "a..b..c", "select": [{"value": "key"}, {"value": "value"}]}
        self.assertEqual(result, expected)

    def test_issue_100_sign_operator(self):
        sql = """SELECT CASE WHEN 1=1 THEN + 1 ELSE - 1 END AS x FROM `a.b.c`"""
        result = parse(sql)
        expected = {
            "from": "a..b..c",
            "select": {"name": "x", "value": {"case": [{"when": {"eq": [1, 1]}, "then": 1}, -1]}},
        }
        self.assertEqual(result, expected)

    def test_issue_156(self):
        sql = """select * FROM (t1 INNER JOIN t2 ON t1.c1 = t2.c2)"""
        result = parse(sql)
        expected = {
            "from": ["t1", {"inner join": "t2", "on": {"eq": ["t1.c1", "t2.c2"]}}],
            "select": "*",
        }
        self.assertEqual(result, expected)

    def test_issue_157_describe(self):
        sql = """describe query plan select * from temp"""
        result = parse(sql)
        expected = {"explain": {"from": "temp", "select": "*"}}
        self.assertEqual(result, expected)

    def test_issue_174_no_from(self):
        sql = """SELECT 1 WHERE TRUE"""
        expected = {"select": {"value": 1}, "where": True}
        result = parse(sql)
        self.assertEqual(result, expected)

    def test_issue_177_select_values_w_alias(self):
        sql = """SELECT value1, value2 FROM (VALUES ('A', 'B'), ('C', 'D'), ('E', 'D')) table (value1, value2)"""
        expected = {
            "from": {
                "name": {"table": ["value1", "value2"]},
                "value": {"from": {"literal": [["A", "B"], ["C", "D"], ["E", "D"]]}},
            },
            "select": [{"value": "value1"}, {"value": "value2"}],
        }

        result = parse(sql)
        self.assertEqual(result, expected)

    def test_issue_203(self):
        sql = """select emp_id, sep_id, programid,
            row_number() over( partition by emp_id order by sep_id desc) as ord
            from bidg_1.crs_fact"""
        expected = {
            "from": "bidg_1.crs_fact",
            "select": [
                {"value": "emp_id"},
                {"value": "sep_id"},
                {"value": "programid"},
                {
                    "name": "ord",
                    "over": {"orderby": {"sort": "desc", "value": "sep_id"}, "partitionby": "emp_id"},
                    "value": {"row_number": {}},
                }
            ]
        }

        result = parse(sql)
        self.assertEqual(result, expected)

    def test_using_all_column_star(self):
        sql = "select * from a join b using (*)"
        result = parse_mysql(sql, null=SQL_NULL, calls=simple_op, all_columns="*")

        expected = {"from": ["a", {"join": "b", "using": "*"}], "select": "*"}
        self.assertEqual(result, expected)

    def test_all_columns_is_column(self):
        sql = "select all_columns, * from a"
        result = parse(sql)
        expected = {"from": "a", "select": [{"value": "all_columns"}, "*"]}
        self.assertEqual(result, expected)
        new_sql = format(result)
        self.assertEqual(new_sql, "SELECT all_columns, * FROM a")

    def test_from_many_tables(self):
        sql = "select * from a, b, c"
        result = parse(sql)
        expected = {"from": ["a", "b", "c"], "select": "*"}
        self.assertEqual(result, expected)
        new_sql = format(result)
        self.assertEqual(new_sql, "SELECT * FROM a, b, c")

    def test_issue_225(self):
        sql = """select invoicedate, cast(year(InvoiceDate) as nchar(4)) +'-'+ cast(month(InvoiceDate) as nvarchar(2)) +'-'+ cast(day(InvoiceDate) as nvarchar(2)) as NewDateFormat from Invoice"""
        result = parse(sql)
        expected = {
            "from": "Invoice",
            "select": [
                {"value": "invoicedate"},
                {
                    "name": "NewDateFormat",
                    "value": {"add": [
                        {"cast": [{"year": "InvoiceDate"}, {"nchar": 4}]},
                        {"literal": "-"},
                        {"cast": [{"month": "InvoiceDate"}, {"nvarchar": 2}]},
                        {"literal": "-"},
                        {"cast": [{"day": "InvoiceDate"}, {"nvarchar": 2}]},
                    ]},
                },
            ],
        }

        self.assertEqual(result, expected)

    def test_issue_230_is_null(self):
        sql = "select id from tbl where id is null"
        result = parse(sql, fmap={"missing": "is_null", "exists": "is_not_null"})
        expected = {"from": "tbl", "select": {"value": "id"}, "where": {"is_null": "id"}}
        self.assertEqual(result, expected)

    def test_issue_257_singleton_list(self):
        sql = """select * from table where table.column in (1);"""
        result = parse(sql)
        expected = {"from": "table", "select": "*", "where": {"in": ["table.column", 1]}}
        self.assertEqual(result, expected)

        new_sql = format(result)
        self.assertEqual(new_sql, "SELECT * FROM table WHERE table.column IN (1)")

    def test_issue_256_singleton_list(self):
        sql = """select *
            from PROD_PIVOT_ME
              pivot (max(event) for act_prod in ('ANY'))"""
        result = parse(sql)
        expected = {
            "from": "PROD_PIVOT_ME",
            "pivot": {"for": "act_prod", "in": {"literal": "ANY"}, "aggregate": {"max": "event"}},
            "select": "*",
        }
        self.assertEqual(result, expected)

