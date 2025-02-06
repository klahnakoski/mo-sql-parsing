# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Author: Beto Dealmeida (beto@dealmeida.net)
#
import re
from unittest import TestCase

from mo_sql_parsing import format, parse, parse_sqlserver


class TestSimple(TestCase):
    def test_two_tables(self):
        result = format({"select": {"all_columns": {}}, "from": ["XYZZY", "ABC"]})
        expected = "SELECT * FROM XYZZY, ABC"
        self.assertEqual(result, expected)

    def test_dot_table_name(self):
        result = format({"select": {"all_columns": {}}, "from": "SYS.XYZZY"})
        expected = "SELECT * FROM SYS.XYZZY"
        self.assertEqual(result, expected)

    def select_one_column(self):
        result = format({"select": [{"value": "A"}], "from": ["dual"]})
        expected = "SELECT A FROM dual"
        self.assertEqual(result, expected)

    def test_select_quote(self):
        result = format({"select": {"value": {"literal": "'"}}, "from": "dual"})
        expected = "SELECT '''' FROM dual"
        self.assertEqual(result, expected)

    def test_select_quoted_name(self):
        result = format({
            "select": [{"name": "@*#&", "value": "a"}, {"name": "test.g.g.c", "value": "b"}],
            "from": "dual",
        })
        expected = 'SELECT a AS "@*#&", b AS test.g.g.c FROM dual'
        self.assertEqual(result, expected)

    def test_select_expression(self):
        result = format({
            "select": {"value": {"add": ["a", {"div": ["b", 2]}, {"mul": [45, "c"]}, {"div": [2, "d"]}]}},
            "from": "dual",
        })
        expected = "SELECT a + b / 2 + 45 * c + 2 / d FROM dual"
        self.assertEqual(result, expected)

    def test_select_underscore_name(self):
        result = format({"select": {"value": "_id"}, "from": "dual"})
        expected = "SELECT _id FROM dual"
        self.assertEqual(result, expected)

    def test_select_dots_names(self):
        result = format({"select": {"value": "a.b.c._d"}, "from": "dual"})
        expected = "SELECT a.b.c._d FROM dual"
        self.assertEqual(result, expected)

    def select_many_column(self):
        result = format({"select": [{"value": "a"}, {"value": "b"}, {"value": "c"}], "from": ["dual"]})
        expected = "SELECT a, b, c FROM dual"
        self.assertEqual(result, expected)

    def test_where_neq(self):
        result = format({"select": {"all_columns": {}}, "from": "dual", "where": {"neq": ["a", {"literal": "test"}]}})
        expected = "SELECT * FROM dual WHERE a <> 'test'"
        self.assertEqual(result, expected)

    def test_where_in(self):
        result = format({
            "select": {"value": "a"},
            "from": "dual",
            "where": {"in": ["a", {"literal": ["r", "g", "b"]}]},
        })
        expected = "SELECT a FROM dual WHERE a IN ('r', 'g', 'b')"
        self.assertEqual(result, expected)

    def test_where_in_and_in(self):
        result = format({
            "select": {"value": "a"},
            "from": "dual",
            "where": {"and": [{"in": ["a", {"literal": ["r", "g", "b"]}]}, {"in": ["b", [10, 11, 12]]}]},
        })
        expected = "SELECT a FROM dual WHERE a IN ('r', 'g', 'b') AND b IN (10, 11, 12)"
        self.assertEqual(result, expected)

    def test_eq(self):
        result = format({
            "select": [{"value": "a"}, {"value": "b"}],
            "from": ["t1", "t2"],
            "where": {"eq": ["t1.a", "t2.b"]},
        })
        expected = "SELECT a, b FROM t1, t2 WHERE t1.a = t2.b"
        self.assertEqual(result, expected)

    def test_is_null(self):
        result = format({"select": [{"value": "a"}, {"value": "b"}], "from": "t1", "where": {"missing": "t1.a"}})
        expected = "SELECT a, b FROM t1 WHERE t1.a IS NULL"
        self.assertEqual(result, expected)

    def test_is_not_null(self):
        result = format({"select": [{"value": "a"}, {"value": "b"}], "from": "t1", "where": {"exists": "t1.a"}})
        expected = "SELECT a, b FROM t1 WHERE t1.a IS NOT NULL"
        self.assertEqual(result, expected)

    def test_groupby(self):
        result = format({
            "select": [{"value": "a"}, {"name": "b", "value": {"count": 1}}],
            "from": "mytable",
            "groupby": {"value": "a"},
        })
        expected = "SELECT a, COUNT(1) AS b FROM mytable GROUP BY a"
        self.assertEqual(result, expected)

    def test_function(self):
        result = format({"select": {"value": {"count": 1}}, "from": "mytable"})
        expected = "SELECT COUNT(1) FROM mytable"
        self.assertEqual(result, expected)

    def test_order_by(self):
        result = format({"select": {"value": {"count": 1}}, "from": "dual", "orderby": {"value": "a"}})
        expected = "SELECT COUNT(1) FROM dual ORDER BY a"
        self.assertEqual(result, expected)

    def test_order_by_asc(self):
        result = format({"select": {"value": {"count": 1}}, "from": "dual", "orderby": {"value": "a", "sort": "asc"}})
        expected = "SELECT COUNT(1) FROM dual ORDER BY a ASC"
        self.assertEqual(result, expected)

    def test_order_by_desc(self):
        result = format({
            "select": {"value": {"count": 1}},
            "from": "dual",
            "orderby": {"value": "a", "sort": "desc"},
        })
        expected = "SELECT COUNT(1) FROM dual ORDER BY a DESC"
        self.assertEqual(result, expected)

    def test_neg_or_precedence(self):
        result = format({
            "from": "table1",
            "where": {"or": [{"eq": ["A", -900]}, {"eq": ["B", 100]}]},
            "select": [{"value": "B"}, {"value": "C"}],
        })
        expected = "SELECT B, C FROM table1 WHERE A = -900 OR B = 100"
        self.assertEqual(result, expected)

    def test_negative_number(self):
        result = format({"from": "table1", "where": {"eq": ["A", -900]}, "select": {"value": "a"}})
        expected = "SELECT a FROM table1 WHERE A = -900"
        self.assertEqual(result, expected)

    def test_like_in_where(self):
        result = format({"from": "table1", "where": {"like": ["A", {"literal": "%20%"}]}, "select": {"value": "a"}})
        expected = "SELECT a FROM table1 WHERE A LIKE '%20%'"
        self.assertEqual(result, expected)

    def test_like_in_select(self):
        result = format({
            "from": "table1",
            "select": {
                "name": "bb",
                "value": {"case": [{"when": {"like": ["A", {"literal": "bb%"}]}, "then": 1}, 0]},
            },
        })
        expected = "SELECT CASE WHEN A LIKE 'bb%' THEN 1 ELSE 0 END AS bb FROM table1"
        self.assertEqual(result, expected)

    def test_like_from_pr16(self):
        result = format({
            "from": "trade",
            "where": {"and": [
                {"like": ["school", {"literal": "%shool"}]},
                {"eq": ["name", {"literal": "abc"}]},
                {"in": ["id", {"literal": ["1", "2"]}]},
            ]},
            "select": {"all_columns": {}},
        })
        expected = "SELECT * FROM trade WHERE school LIKE '%shool' AND name = 'abc' AND id IN ('1', '2')"
        self.assertEqual(result, expected)

    def test_rlike_in_where(self):
        result = format({
            "from": "table1",
            "where": {"rlike": ["A", {"literal": ".*20.*"}]},
            "select": {"value": "a"},
        })
        expected = "SELECT a FROM table1 WHERE A RLIKE '.*20.*'"
        self.assertEqual(result, expected)

    def test_rlike_in_select(self):
        result = format({
            "from": "table1",
            "select": {
                "name": "bb",
                "value": {"case": [{"when": {"rlike": ["A", {"literal": "bb.*"}]}, "then": 1}, 0]},
            },
        })
        expected = "SELECT CASE WHEN A RLIKE 'bb.*' THEN 1 ELSE 0 END AS bb FROM table1"
        self.assertEqual(result, expected)

    def test_in_expression(self):
        result = format({
            "from": "task",
            "select": {"all_columns": {}},
            "where": {"in": ["repo.branch.name", {"literal": ["try", "mozilla-central"]}]},
        })
        expected = "SELECT * FROM task WHERE repo.branch.name IN ('try', 'mozilla-central')"
        self.assertEqual(result, expected)

    def test_joined_table_name(self):
        result = format({
            "from": [
                {"name": "t1", "value": "table1"},
                {"on": {"eq": ["t1.id", "t3.id"]}, "join": {"name": "t3", "value": "table3"}},
            ],
            "select": {"all_columns": {}},
        })
        expected = "SELECT * FROM table1 AS t1 JOIN table3 AS t3 ON t1.id = t3.id"
        self.assertEqual(result, expected)

    def test_not_equal(self):
        result = format({
            "select": {"all_columns": {}},
            "from": "task",
            "where": {"and": [{"exists": "build.product"}, {"neq": ["build.product", {"literal": "firefox"}]}]},
        })
        expected = "SELECT * FROM task WHERE build.product IS NOT NULL AND build.product <> 'firefox'"
        self.assertEqual(result, expected)

    def test_union(self):
        result = format({"union": [
            {"select": {"all_columns": {}}, "from": "a"},
            {"select": {"all_columns": {}}, "from": "b"},
        ]})
        expected = "SELECT * FROM a\nUNION\nSELECT * FROM b"
        self.assertEqual(result, expected)

    def test_limit(self):
        result = format({"select": {"all_columns": {}}, "from": "a", "limit": 10})
        expected = "SELECT * FROM a LIMIT 10"
        self.assertEqual(result, expected)

    def test_offset(self):
        result = format({"select": {"all_columns": {}}, "from": "a", "limit": 10, "offset": 10})
        expected = "SELECT * FROM a LIMIT 10 OFFSET 10"
        self.assertEqual(result, expected)

    def test_count_literal(self):
        result = format({"select": {"value": {"count": {"literal": "literal"}}}, "from": "a"})
        expected = "SELECT COUNT('literal') FROM a"
        self.assertEqual(result, expected)

    def test_no_arguments(self):
        result = format({"select": {"value": {"now": {}}}})
        expected = "SELECT NOW()"
        self.assertEqual(result, expected)

    def test_between(self):
        result = format({
            "select": [{"value": "a"}],
            "from": ["t1"],
            "where": {"between": ["t1.a", 10, {"literal": "ABC"}]},
        })
        expected = "SELECT a FROM t1 WHERE t1.a BETWEEN 10 AND 'ABC'"
        self.assertEqual(result, expected)

    def test_binary_and(self):
        expected = "SELECT * FROM t WHERE c & 4"
        result = format({"select": {"all_columns": {}}, "from": "t", "where": {"binary_and": ["c", 4]}})
        self.assertEqual(result, expected)

    def test_binary_or(self):
        expected = "SELECT * FROM t WHERE c | 4"
        result = format({"select": {"all_columns": {}}, "from": "t", "where": {"binary_or": ["c", 4]}})
        self.assertEqual(result, expected)

    def test_binary_not(self):
        expected = "SELECT * FROM t WHERE ~c"
        result = format({"select": {"all_columns": {}}, "from": "t", "where": {"binary_not": "c"}})
        self.assertEqual(result, expected)

    def test_issue_104(self):
        expected = (
            'SELECT NomPropriete AS Categorie, ROUND(AVG(NotePonderee), 2) AS "Moyenne'
            ' des notes", ROUND(AVG(Complexite), 2) AS "Complexite moyenne" FROM'
            " Propriete, Categorie, Jeu WHERE IdPropriete = IdCategorie AND"
            " Categorie.IdJeu = Jeu.IdJeu AND NotePonderee > 0 GROUP BY IdPropriete,"
            ' NomPropriete ORDER BY "Moyenne des notes" DESC, "Complexite moyenne" DESC'
        )
        result = format({
            "select": [
                {"value": "NomPropriete", "name": "Categorie"},
                {"value": {"round": [{"avg": "NotePonderee"}, 2]}, "name": "Moyenne des notes"},
                {"value": {"round": [{"avg": "Complexite"}, 2]}, "name": "Complexite moyenne"},
            ],
            "from": ["Propriete", "Categorie", "Jeu"],
            "where": {"and": [
                {"eq": ["IdPropriete", "IdCategorie"]},
                {"eq": ["Categorie.IdJeu", "Jeu.IdJeu"]},
                {"gt": ["NotePonderee", 0]},
            ]},
            "groupby": [{"value": "IdPropriete"}, {"value": "NomPropriete"}],
            "orderby": [
                {"value": "Moyenne des notes", "sort": "desc"},
                {"value": "Complexite moyenne", "sort": "desc"},
            ],
        })
        self.assertEqual(result, expected)

    def test_with_cte(self):
        expected = "WITH t AS (\nSELECT a FROM table\n) SELECT * FROM t"
        result = format({
            "select": {"all_columns": {}},
            "from": "t",
            "with": {"name": "t", "value": {"select": {"value": "a"}, "from": "table"}},
        })
        self.assertEqual(result, expected)

    def test_with_cte_various(self):
        expected = "WITH t1 AS (\nSELECT a FROM table\n), t2 AS (\nSELECT 1\n) SELECT * FROM t1, t2"
        result = format({
            "select": {"all_columns": {}},
            "from": ["t1", "t2"],
            "with": [
                {"name": "t1", "value": {"select": {"value": "a"}, "from": "table"}},
                {"name": "t2", "value": {"select": {"value": 1}}},
            ],
        })
        self.assertEqual(result, expected)

    def test_concat(self):
        expected = "SELECT CONCAT('a', 'a')"
        result = format({"select": {"value": {"concat": [{"literal": "a"}, {"literal": "a"}]}}})
        self.assertEqual(result, expected)

    def test_issue_28(self):
        original_sql = "select * from T where (a, b) in (('a', 'b'), ('c', 'd'))"
        parse_result = parse(original_sql)
        expected_result = {
            "select": {"all_columns": {}},
            "from": "T",
            "where": {"in": [["a", "b"], {"literal": [["a", "b"], ["c", "d"]]}]},
        }
        self.assertEqual(parse_result, expected_result)

        expected_sql = "SELECT * FROM T WHERE (a, b) IN (('a', 'b'), ('c', 'd'))"
        format_result = format(expected_result)
        self.assertEqual(format_result, expected_sql)

    def test_issue_34_intersect(self):
        query = "SELECT stuid FROM student INTERSECT SELECT stuid FROM student"
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_34_union_all(self):
        query = "SELECT stuid FROM student\nUNION ALL\nSELECT stuid FROM student"
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_36_lost_parenthesis(self):
        query = """SELECT COUNT(*) FROM (SELECT city FROM airports GROUP BY city HAVING COUNT(*) > 3)"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_35_distinct(self):
        query = "SELECT DISTINCT a, b FROM t"
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_37_parenthesis1(self):
        query = """SELECT name FROM stadium WHERE stadium_id NOT IN (SELECT stadium_id FROM concert)"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_37_parenthesis2(self):
        query = (
            """SELECT rid FROM routes WHERE dst_apid IN (SELECT apid FROM airports WHERE country = 'United States')"""
        )
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_37_parenthesis3(self):
        query = """SELECT COUNT(*) FROM (SELECT cName FROM tryout INTERSECT SELECT cName FROM tryout)"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_found_in_sparqling_queries1(self):
        # https://github.com/yandex-research/sparqling-queries/blob/e04d0bfd507c4859be3f35d4e0d8eb57434bb4f6/data/spider

        query = """SELECT name, date FROM battle"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)
        query = (
            """SELECT first_name FROM Professionals\nUNION\nSELECT first_name FROM Owners EXCEPT SELECT name FROM Dogs"""
        )
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)
        query = """SELECT date FROM weather WHERE max_temperature_f > 85"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)
        query = """SELECT zip_code, AVG(mean_temperature_f) FROM weather WHERE date LIKE '8/%' GROUP BY zip_code"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)
        query = """SELECT text FROM tweets WHERE text LIKE '%intern%'"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)
        query = """SELECT river_name FROM river GROUP BY river_name ORDER BY COUNT(DISTINCT traverse) DESC LIMIT 1"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)
        query = """SELECT DISTINCT t1.paperid, COUNT(t3.citingpaperid) FROM paper AS t1 JOIN cite AS t3 ON t1.paperid = t3.citedpaperid JOIN venue AS t2 ON t2.venueid = t1.venueid WHERE t1.year = 2012 AND t2.venuename = 'ACL' GROUP BY t1.paperid HAVING COUNT(t3.citingpaperid) > 7"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)
        query = """SELECT TIME FROM elimination WHERE Eliminated_By = 'Punk' OR Eliminated_By = 'Orton'"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)
        query = """SELECT hire_date FROM employees WHERE first_name NOT LIKE '%M%'"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_found_in_sparqling_queries2(self):
        query = """SELECT document_name FROM documents GROUP BY document_type_code INTERSECT SELECT document_name FROM documents GROUP BY document_structure_code ORDER BY COUNT(*) DESC LIMIT 3"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

        query = """SELECT t1.name FROM CAST AS t2 JOIN actor AS t1 ON t2.aid = t1.aid JOIN movie AS t3 ON t3.mid = t2.msid WHERE t2.role = 'Alan Turing' AND t3.title = 'The Imitation Game'"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_38_not_like(self):
        query = """SELECT hire_date FROM employees WHERE first_name NOT LIKE '%M%'"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_40_over_clause(self):
        query = """SELECT name, dept, RANK() OVER (PARTITION BY dept ORDER BY salary) AS rank FROM employees"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_40_indow_function1(self):
        query = """select sum(qty) over (order by a rows between 1 preceding and 2 following)""".upper()
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_40_window_function2(self):
        query = """select sum(qty) over (order by a rows between 3 preceding and 1 preceding)""".upper()
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_40_window_function3(self):
        query = """select sum(qty) over (order by a rows between 3 following and 5 following)""".upper()
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_40_window_function4(self):
        query = """select sum(qty) over (order by a rows between 3 following and unbounded following)""".upper()
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_40_window_function5(self):
        query = """select sum(qty) over (order by a rows 3 following)""".upper()
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_41_distinct_on(self):
        query = """SELECT DISTINCT ON (col) col, col2 FROM test"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, query)

    def test_issue_41_cast_as(self):
        query = """select cast(10.008 AS DECIMAL(10,2))"""
        parse_result = parse(query)
        format_result = format(parse_result)
        self.assertEqual(format_result, """SELECT CAST(10.008 AS DECIMAL(10, 2))""")

    def test_issues_45_cast(self):
        sql = """select node,datetime from e where ((900 - ( cast(p as FLOAT) + cast(p as FLOAT) ) ) / 900) < 0.9 order by datetime limit 100"""
        result = parse(sql)
        parsed_query = {
            "from": "e",
            "limit": 100,
            "orderby": {"value": "datetime"},
            "select": [{"value": "node"}, {"value": "datetime"}],
            "where": {"lt": [
                {"div": [
                    {"sub": [900, {"add": [{"cast": ["p", {"float": {}}]}, {"cast": ["p", {"float": {}}]}]}]},
                    900,
                ]},
                0.9,
            ]},
        }
        self.assertEqual(result, parsed_query)

        re_format_query = format(result)
        self.assertEqual(
            re_format_query,
            """SELECT node, datetime FROM e WHERE (900 - (CAST(p AS FLOAT) + CAST(p AS FLOAT))) / 900 < 0.9 ORDER BY datetime LIMIT 100""",
        )

    def test_issue_47_precedence(self):
        sql = """SELECT c1, c2 FROM t1 WHERE ((900 - (CAST(c3 AS FLOAT) + CAST(c4 AS FLOAT))) / 900) < 0.9 ORDER BY c2 LIMIT 100"""
        expected_sql = """SELECT c1, c2 FROM t1 WHERE (900 - (CAST(c3 AS FLOAT) + CAST(c4 AS FLOAT))) / 900 < 0.9 ORDER BY c2 LIMIT 100"""

        result = parse(sql)
        expected_result = {
            "from": "t1",
            "limit": 100,
            "orderby": {"value": "c2"},
            "select": [{"value": "c1"}, {"value": "c2"}],
            "where": {"lt": [
                {"div": [
                    {"sub": [900, {"add": [{"cast": ["c3", {"float": {}}]}, {"cast": ["c4", {"float": {}}]}]}]},
                    900,
                ]},
                0.9,
            ]},
        }
        self.assertEqual(result, expected_result)
        format_result = format(result)
        self.assertEqual(format_result, expected_sql)

        second_result = parse(sql)
        self.assertEqual(second_result, expected_result)

    def test_issue_50_dashes_in_names(self):
        sql = """select `col-cpu-usage` from `test-information`"""
        result = parse(sql)
        new_sql = format(result)
        expected = 'SELECT "col-cpu-usage" FROM "test-information"'
        self.assertEqual(new_sql, expected)

    def test_issue_51_interval(self):
        result = format(parse("select now() + interval 2 week"))
        expected = "SELECT NOW() + INTERVAL '2' WEEK"
        self.assertEqual(result, expected)

    def test_issue_51_interval_string(self):
        result = format(parse("select now() + interval '2' week"))
        expected = "SELECT NOW() + INTERVAL '2' WEEK"
        self.assertEqual(result, expected)

    def test_issue_51_interval_string2(self):
        result = format(parse("select now() + interval '2 week'"))
        expected = "SELECT NOW() + INTERVAL '2' WEEK"
        self.assertEqual(result, expected)

    def test_issue_51_interval_string3(self):
        result = format(parse("select now() + interval '1.5' second"))
        expected = "SELECT NOW() + INTERVAL '1.5' SECOND"
        self.assertEqual(result, expected)

    def test_issue_51_interval_float(self):
        result = format(parse("select now() + interval 1.5 second"))
        expected = "SELECT NOW() + INTERVAL '1.5' SECOND"
        self.assertEqual(result, expected)

    def test_issue_51_interval_expression(self):
        result = format(parse("select now() + interval (1+1) week"))
        expected = "SELECT NOW() + INTERVAL (1 + 1) WEEK"
        self.assertEqual(result, expected)

    def test_issue_65_parenthesis(self):
        sql = """Select * from abc a inner join (select * from def) b on a.id = b.id"""
        result = format(parse(sql))
        expected = """SELECT * FROM abc AS a INNER JOIN (SELECT * FROM def) AS b ON a.id = b.id"""
        self.assertEqual(result, expected)

    def test_issue_64_format_insert(self):
        sql = """INSERT INTO Person(Id, Name, DateOfBirth, Gender)
            VALUES (1, 'John Lennon', '1940-10-09', 'M'), (2, 'Paul McCartney', '1942-06-18', 'M'),
            (3, 'George Harrison', '1943-02-25', 'M'), (4, 'Ringo Starr', '1940-07-07', 'M')"""
        result = format(parse(sql))
        expected = """INSERT INTO Person (DateOfBirth, Gender, Id, Name) VALUES ('1940-10-09', 'M', 1, 'John Lennon'),\n('1942-06-18', 'M', 2, 'Paul McCartney'),\n('1943-02-25', 'M', 3, 'George Harrison'),\n('1940-07-07', 'M', 4, 'Ringo Starr')"""
        self.assertEqual(result, expected)

    def test_issue_66_single_item_in_list1(self):
        sql = """SELECT * FROM my_table WHERE outcome NOT IN ('COMPLETED')"""
        result = format(parse(sql))
        expected = """SELECT * FROM my_table WHERE outcome NOT IN ('COMPLETED')"""
        self.assertEqual(result, expected)

    def test_issue_66_single_item_in_list2(self):
        sql = """SELECT * FROM my_table WHERE outcome IN ('COMPLETED')"""
        result = format(parse(sql))
        expected = """SELECT * FROM my_table WHERE outcome IN ('COMPLETED')"""
        self.assertEqual(result, expected)

    def test_issue_66_single_item_in_list3(self):
        sql = """SELECT * FROM my_table WHERE outcome IN (SELECT a FROM b)"""
        result = format(parse(sql))
        expected = """SELECT * FROM my_table WHERE outcome IN (SELECT a FROM b)"""
        self.assertEqual(result, expected)

    def test_issue68_grouping_numbers(self):
        sql = "SELECT * FROM mytable WHERE (a, b) IN ((1, 2), (3,4))"
        p = parse(sql)
        s = format(p)
        self.assertEqual(
            p, {"from": "mytable", "select": {"all_columns": {}}, "where": {"in": [["a", "b"], [[1, 2], [3, 4]]]}},
        )
        self.assertEqual(s, "SELECT * FROM mytable WHERE (a, b) IN ((1, 2), (3, 4))")

    def test_issue68_group_strings(self):
        sql = """SELECT * FROM AirlineFlights WHERE (origin, dest) IN (('ATL', 'ABE'), ('DFW', 'ABI'))"""
        p = parse(sql)
        s = format(p)
        self.assertEqual(
            p,
            {
                "from": "AirlineFlights",
                "select": {"all_columns": {}},
                "where": {"in": [["origin", "dest"], {"literal": [["ATL", "ABE"], ["DFW", "ABI"]]}]},
            },
        )
        self.assertEqual(
            s, """SELECT * FROM AirlineFlights WHERE (origin, dest) IN (('ATL', 'ABE'), ('DFW', 'ABI'))""",
        )

    def test_issue_69_format_array_access(self):
        sql = """SELECT nested_0.parentsList.datasetPathList[2] FROM mytable_with_complex_cols"""
        s = format(parse(sql))
        self.assertEqual(
            s, """SELECT nested_0.parentsList.datasetPathList[2] FROM mytable_with_complex_cols""",
        )

    def test_issue_73_extract_formatting(self):
        s = format(parse("""SELECT EXTRACT(DAY FROM DATE'2019-08-17')"""))
        self.assertEqual(s, """SELECT EXTRACT(DAY FROM DATE('2019-08-17'))""")

    def test_issue_81_concat(self):
        new_sql = format(parse("SELECT 'str1' || 'str2' || my_int_field from testtable"))
        self.assertEqual(
            new_sql, "SELECT CONCAT('str1', 'str2', my_int_field) FROM testtable",
        )

        new_sql = format(parse("SELECT concat('str1', 'str2', my_int_field) from testtable"))
        self.assertEqual(new_sql, "SELECT CONCAT('str1', 'str2', my_int_field) FROM testtable")

    def test_isssue_82_partition_list(self):
        sql = """SELECT FIELD1, RANK() OVER (PARTITION BY "FIELD2", "FIELD3" ORDER BY FIELD5, FIELD6) AS NEWFIELD from testtable"""
        new_sql = format(parse(sql))
        self.assertEqual(
            new_sql,
            """SELECT FIELD1, RANK() OVER (PARTITION BY FIELD2, FIELD3 ORDER BY FIELD5, FIELD6) AS NEWFIELD FROM testtable""",
        )

    def test_issue_87_loss_of_brackets(self):
        sql = """SELECT (SELECT COUNT(result) FROM dbo.b AS B) as attr FROM dbo.table"""
        new_sql = format(parse(sql))
        self.assertEqual(
            new_sql, """SELECT (SELECT COUNT(result) FROM dbo.b AS B) AS attr FROM dbo.table""",
        )

    def test_table_sample1(self):
        sql = "SELECT * FROM foo SAMPLE bernoulli (1)"
        new_sql = format(parse(sql))
        self.assertEqual(new_sql, "SELECT * FROM foo TABLESAMPLE bernoulli (1 PERCENT)")

        sql = "SELECT * FROM foo SAMPLE(1) WHERE a < 42"
        new_sql = format(parse(sql))
        self.assertEqual(new_sql, "SELECT * FROM foo TABLESAMPLE (1 PERCENT) WHERE a < 42")

        sql = "SELECT * FROM foo TABLESAMPLE bernoulli (1)"
        new_sql = format(parse(sql))
        self.assertEqual(new_sql, "SELECT * FROM foo TABLESAMPLE bernoulli (1 PERCENT)")

        sql = "SELECT * FROM foo f TABLESAMPLE bernoulli (1) WHERE f.a < 42"
        new_sql = format(parse(sql))
        self.assertEqual(
            new_sql, "SELECT * FROM foo AS f TABLESAMPLE bernoulli (1 PERCENT) WHERE f.a < 42",
        )

    def test_table_sample2(self):
        sql = """SELECT a FROM test TABLESAMPLE (BUCKET 1 OUT OF 5)"""
        new_sql = format(parse(sql))
        self.assertEqual(new_sql, sql)

        sql = """SELECT a FROM test TABLESAMPLE (BUCKET 1 OUT OF 5 ON x)"""
        new_sql = format(parse(sql))
        self.assertEqual(new_sql, sql)

        sql = """SELECT a FROM test TABLESAMPLE (BUCKET 1 OUT OF 5 ON RAND())"""
        new_sql = format(parse(sql))
        self.assertEqual(new_sql, sql)

        sql = """SELECT a FROM test TABLESAMPLE (0.1 PERCENT)"""
        new_sql = format(parse(sql))
        self.assertEqual(new_sql, sql)

    def test_table_sample3(self):
        sql = """SELECT a FROM test TABLESAMPLE (100 ROWS)"""
        new_sql = format(parse(sql))
        self.assertEqual(new_sql, sql)

    def test_issue_146(self):
        parsed = {
            "from": "customer",
            "where": {"in": [
                {"from": 1, "for": 2, "substring": "c_phone"},
                {"literal": ["28", "27", "17", "10", "14", "34", "15"]},
            ]},
        }
        sql = format(parsed)
        self.assertEqual(
            sql,
            """FROM customer WHERE SUBSTRING(c_phone FROM 1 FOR 2) IN ('28', '27', '17', '10', '14', '34', '15')""",
        )

    def test_issue_136(self):
        sql = """SELECT * FROM T1 WHERE NOT EXISTS (SELECT * FROM T1,T2 WHERE T1.C1=T2.C2)"""
        result = parse(sql)
        new_sql = format(result)
        self.assertEqual(
            new_sql, """SELECT * FROM T1 WHERE NOT EXISTS (SELECT * FROM T1, T2 WHERE T1.C1 = T2.C2)""",
        )

    def test_issue_137_delete(self):
        formatted = format({"delete": "x", "where": {"gt": ["y", 1]}})
        self.assertEqual(formatted, """DELETE FROM x\nWHERE y > 1""")

    def test_issue_142_agg_functions(self):
        sql = """SELECT ARRAY_AGG(DISTINCT x IGNORE NULLS ORDER BY x LIMIT 1)"""
        formatted = format(parse(sql))
        self.assertEqual(formatted, sql)

    def test_issue_148_filter_format(self):
        sql = """SELECT MAX(1) FILTER (WHERE 1 = 1) AS foo"""
        result = parse(sql)
        expected = {"select": {"filter": {"eq": [1, 1]}, "name": "foo", "value": {"max": 1}}}
        self.assertEqual(result, expected)
        formatted = format(parse(sql))
        self.assertEqual(formatted, sql)

    def test_issue_158_format_substring(self):
        sql = """SELECT CASE WHEN a.attr1 IS NULL THEN CONCAT(SUBSTRING(CONVERT(CHAR(7), attr2 + 1000000), 2, 6), SUBSTRING(CONVERT(CHAR(8), attr3 + 10000000), 2, 7)) ELSE a.attr1 END AS alias1 FROM schema.table AS a"""
        result = parse(sql)
        formatted = format(parse(sql))
        self.assertEqual(formatted, sql)

    def test_try_cast_format_back(self):
        sql = """SELECT TRY_CAST(a AS DECIMAL(10, 3)) FROM b.c"""
        result = parse(sql)
        formatted = format(parse(sql))
        self.assertEqual(formatted, sql)

    def test_validate_conversion_format_back(self):
        sql = """SELECT VALIDATE_CONVERSION(a AS DECIMAL(10, 3)) FROM b.c"""
        result = parse(sql)
        formatted = format(parse(sql))
        self.assertEqual(formatted, sql)

    def test_subquery_as_param_format_back(self):
        sql = """SELECT DATEDIFF(mm, col2, (SELECT MAX(col) FROM dbo.table)) AS A FROM be"""
        result = parse(sql)
        formatted = format(parse(sql))
        self.assertEqual(formatted, sql)

    def test_issue_177_format_select_values_w_alias(self):
        sql = """SELECT value1, value2 FROM (VALUES ('A', 'B'), ('C', 'D'), ('E', 'D')) table (value1, value2)"""
        expected = (
            """SELECT value1, value2 FROM (VALUES ('A', 'B'), ('C', 'D'), ('E', 'D')) AS TABLE(value1, value2)"""
        )
        result = format(parse(sql))
        self.assertEqual(result, expected)

    def test_issue_181_select_distinct(self):
        sql = """select distinct (SELECT GETDATE() as dd) as currentdate"""
        expected = """SELECT DISTINCT (SELECT GETDATE() AS dd) AS currentdate"""
        result = format(parse(sql))
        self.assertEqual(result, expected)

    def test_regexp_formated(self):
        sql = """SELECT * FROM dbo.table WHERE col REGEXP '[^0-9A-Za-z]'"""
        expected = """SELECT * FROM dbo.table WHERE col REGEXP '[^0-9A-Za-z]'"""
        result = format(parse(sql))
        self.assertEqual(result, expected)

    def test_not_regexp_formated(self):
        sql = """SELECT * FROM dbo.table WHERE col NOT REGEXP '[^0-9A-Za-z]'"""
        expected = """SELECT * FROM dbo.table WHERE col NOT REGEXP '[^0-9A-Za-z]'"""
        result = format(parse(sql))
        self.assertEqual(result, expected)

    def test_issue_195_format_group_concat(self):
        sql = "SELECT group_concat(u.co_id order by u.created DESC separator ',')"
        expected = "SELECT group_concat(u.co_id ORDER BY u.created DESC SEPARATOR ',')"
        result = format(parse(sql))
        self.assertEqual(result, expected)

    def test_nliteral_format(self):
        sql = "SELECT * FROM dbo.table WHERE a = N'Something'"
        result = format(parse_sqlserver(sql))
        self.assertEqual(result, sql)

    def test_issue_217(self):
        sql = """SELECT * FROM `dataset_field`  where dataset_field.`id` in (NULL)"""
        result = format(parse(sql))
        expected = """SELECT * FROM dataset_field WHERE dataset_field.id IN (NULL)"""
        self.assertEqual(result, expected)

    def test_issue_220(self):
        sql = """SELECT TO_TIMESTAMP(A DEFAULT NULL ON CONVERSION ERROR, 'DD/MM/YYYY HH24:MI:SS') FROM B.C"""
        result = format(parse(sql))
        self.assertEqual(result, sql)

    def test_issue_233_format_union_all(self):
        sql = """WITH table_test AS (\nSELECT public.categories.string_agg AS string_agg FROM public.categories\n) SELECT * FROM table_test\nUNION ALL\nSELECT * FROM table_test"""
        result = format(parse(sql))
        self.assertEqual(result, sql)

    def test_issue_233_format_union(self):
        sql = """WITH table_test AS (\nSELECT public.categories.string_agg AS string_agg FROM public.categories\n) SELECT * FROM table_test\nUNION\nSELECT * FROM table_test"""
        result = format(parse(sql))
        self.assertEqual(result, sql)

    def test_issue_258_lost_brackets_mini1(self):
        sql = """SELECT a - b - (c - d)"""
        result = format(parse(sql))
        self.assertEqual(result, sql)

    def test_issue_258_lost_brackets_mini2(self):
        sql = "SELECT a - (b + c)"
        result = format(parse(sql))
        self.assertEqual(result, sql)

    def test_issue_258_lost_brackets_mini3(self):
        sql = "SELECT a + b - c"
        result = format(parse(sql))
        self.assertEqual(result, sql)

    def test_issue_258_lost_brackets(self):
        sql = """
        SELECT ROUND(COALESCE(
             (
                 (COUNT(CASE
                        WHEN
                            "public"."polls"."F1" >=
                            9 THEN 1 END) * 100.0 /
                  NULLIF(COUNT("public"."polls"."id"), 0)) -
                 (COUNT(CASE
                            WHEN
                                "public"."polls"."F1" <=
                                6 THEN 1 END) * 100.0 /
                  NULLIF(COUNT("public"."polls"."id"), 0))
            ) -
            (
                 (COUNT(CASE
                            WHEN
                                "public"."polls2"."F1" >=
                                9 THEN 1 END) * 100.0 /
                  NULLIF(COUNT("public"."polls2"."id"), 0)) -
                  (COUNT(CASE
                            WHEN
                                "public"."polls2"."F1" <=
                                6 THEN 1 END) * 100.0 /
                   NULLIF(COUNT("public"."polls2"."id"), 0)
                  )
            ), 0), 2) AS "vcol"
        FROM "public"."polls2"
                 LEFT JOIN "public"."polls" ON "public"."polls2"."id" = "public"."polls"."id"
        WHERE "public"."polls2"."F1" IS NOT NULL
          AND "public"."polls"."F1" IS NOT NULL;"""
        result = format(parse(sql))

        expected = """
            SELECT 
                ROUND(COALESCE(
                    COUNT(CASE WHEN public.polls.F1 >= 9 THEN 1 END) * 100.0 / NULLIF(COUNT(public.polls.id), 0)
                    - COUNT(CASE WHEN public.polls.F1 <= 6 THEN 1 END) * 100.0 / NULLIF(COUNT(public.polls.id), 0)
                    - (
                        COUNT(CASE WHEN public.polls2.F1 >= 9 THEN 1 END) * 100.0 / NULLIF(COUNT(public.polls2.id), 0) 
                        - COUNT(CASE WHEN public.polls2.F1 <= 6 THEN 1 END) * 100.0 / NULLIF(COUNT(public.polls2.id), 0)
                      ), 
                    0
                ), 2) AS vcol 
            FROM 
                public.polls2 
            LEFT JOIN public.polls ON public.polls2.id = public.polls.id 
            WHERE 
                public.polls2.F1 IS NOT NULL AND 
                public.polls.F1 IS NOT NULL
        """
        expected = re.sub(r"\s+", " ",  expected).replace("( ", "(").replace(" )", ")").strip()
        self.assertEqual(result, expected)