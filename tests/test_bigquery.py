# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from unittest import TestCase, skip

from mo_testing.fuzzytestcase import FuzzyTestCase, add_error_reporting

from mo_sql_parsing import parse_bigquery as parse, format


@add_error_reporting
class TestBigQuery(TestCase):
    maxDiff = None

    def test_with_expression(self):
        # https://github.com/pyparsing/pyparsing/issues/291
        sql = """with t as (CASE EXTRACT(dayofweek FROM CURRENT_DATETIME()) when 1 then "S" end) select * from t"""
        result = parse(sql)
        expected = {
            "from": "t",
            "select": "*",
            "with": {
                "name": "t",
                "value": {"case": {
                    "then": {"literal": "S"},
                    "when": {"eq": [{"extract": ["dow", {"current_datetime": {}}]}, 1]},
                }},
            },
        }
        self.assertEqual(result, expected)

    def testA(self):
        sql = """SELECT FIRST_VALUE(finish_time) OVER w1 AS fastest_time"""
        result = parse(sql)
        expected = {"select": {"name": "fastest_time", "over": "w1", "value": {"first_value": "finish_time"}}}
        self.assertEqual(result, expected)

    def testB(self):
        sql = """
          SELECT 
            name,
            FIRST_VALUE(finish_time) OVER w1 AS fastest_time,
            NTH_VALUE(finish_time, 2) OVER w1 as second_fastest
          FROM finishers
          WINDOW w1 AS (
            PARTITION BY division ORDER BY finish_time ASC
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
          )
        """
        result = parse(sql)
        expected = {
            "from": "finishers",
            "window": {
                "name": "w1",
                "value": {"orderby": {"sort": "asc", "value": "finish_time"}, "partitionby": "division", "range": {},},
            },
            "select": [
                {"value": "name"},
                {"name": "fastest_time", "over": "w1", "value": {"first_value": "finish_time"}},
                {"name": "second_fastest", "over": "w1", "value": {"nth_value": ["finish_time", 2]}},
            ],
        }
        self.assertEqual(result, expected)

    def testF(self):
        sql = """
            SELECT
              PERCENTILE_CONT(x, 0) OVER() AS min,
              PERCENTILE_CONT(x, 0.01) OVER() AS percentile1,
              PERCENTILE_CONT(x, 0.5) OVER() AS median,
              PERCENTILE_CONT(x, 0.9) OVER() AS percentile90,
              PERCENTILE_CONT(x, 1) OVER() AS max
            FROM UNNEST([0, 3, NULL, 1, 2]) AS x LIMIT 1
            """
        result = parse(sql)
        expected = {
            "from": {"name": "x", "value": {"unnest": {"create_array": [0, 3, {"null": {}}, 1, 2]}}},
            "limit": 1,
            "select": [
                {"name": "min", "over": {}, "value": {"percentile_cont": ["x", 0]}},
                {"name": "percentile1", "over": {}, "value": {"percentile_cont": ["x", 0.01]}},
                {"name": "median", "over": {}, "value": {"percentile_cont": ["x", 0.5]}},
                {"name": "percentile90", "over": {}, "value": {"percentile_cont": ["x", 0.9]}},
                {"name": "max", "over": {}, "value": {"percentile_cont": ["x", 1]}},
            ],
        }
        self.assertEqual(result, expected)

    def testG(self):
        sql = """
               SELECT
                 x,
                 PERCENTILE_DISC(x, 0) OVER() AS min,
                 PERCENTILE_DISC(x, 0.5) OVER() AS median,
                 PERCENTILE_DISC(x, 1) OVER() AS max
               FROM UNNEST(['c', NULL, 'b', 'a']) AS x
               """
        result = parse(sql)
        expected = {
            "from": {
                "name": "x",
                "value": {"unnest": {"create_array": [
                    {"literal": "c"},
                    {"null": {}},
                    {"literal": "b"},
                    {"literal": "a"},
                ]}},
            },
            "select": [
                {"value": "x"},
                {"name": "min", "over": {}, "value": {"percentile_disc": ["x", 0]}},
                {"name": "median", "over": {}, "value": {"percentile_disc": ["x", 0.5]}},
                {"name": "max", "over": {}, "value": {"percentile_disc": ["x", 1]}},
            ],
        }

        self.assertEqual(result, expected)

    def testL(self):
        sql = """SELECT PERCENTILE_DISC(x, 0) OVER() AS min"""
        result = parse(sql)
        expected = {"select": {"name": "min", "value": {"percentile_disc": ["x", 0]}, "over": {}}}
        self.assertEqual(result, expected)

    def testI_simple(self):
        sql = """
             SELECT
                [
                    STRUCT(
                        " 00:00:00 UTC" as hrs,
                        GENERATE_DATE_ARRAY('2016-01-01', current_date(), INTERVAL 1 DAY) as dt_range
                    )
                ] AS full_timestamps
            """
        result = parse(sql)
        expected = {"select": {
            "name": "full_timestamps",
            "value": {
                "create_array": {"create_struct": [
                    {"name": "hrs", "value": {"literal": " 00:00:00 UTC"}},
                    {
                        "name": "dt_range",
                        "value": {"generate_date_array": [
                            {"literal": "2016-01-01"},
                            {"current_date": {}},
                            {"interval": [1, "day"]},
                        ]},
                    },
                ]},
            },
        }}
        self.assertEqual(result, expected)

    def testI(self):
        sql = """
            WITH date_hour_slots AS (
             SELECT
                [
                    STRUCT(
                        " 00:00:00 UTC" as hrs,
                        GENERATE_DATE_ARRAY('2016-01-01', current_date(), INTERVAL 1 DAY) as dt_range
                    ),
                    STRUCT(
                        " 01:00:00 UTC" as hrs,
                        GENERATE_DATE_ARRAY('2016-01-01',current_date(), INTERVAL 1 DAY) as dt_range
                    )
                ] AS full_timestamps
            )
            SELECT
                dt AS dates, 
                hrs, 
                CAST(CONCAT( CAST(dt as STRING), CAST(hrs as STRING)) as TIMESTAMP) as timestamp_value
            FROM 
                `date_hour_slots`, 
                date_hour_slots.full_timestamps 
            LEFT JOIN 
                full_timestamps.dt_range as dt
            """
        result = parse(sql)
        expected = {
            "from": [
                "date_hour_slots",
                "date_hour_slots.full_timestamps",
                {"left join": {"name": "dt", "value": "full_timestamps.dt_range"}},
            ],
            "select": [
                {"name": "dates", "value": "dt"},
                {"value": "hrs"},
                {
                    "name": "timestamp_value",
                    "value": {"cast": [
                        {"concat": [{"cast": ["dt", {"string": {}}]}, {"cast": ["hrs", {"string": {}}]}]},
                        {"timestamp": {}},
                    ]},
                },
            ],
            "with": {
                "name": "date_hour_slots",
                "value": {"select": {
                    "name": "full_timestamps",
                    "value": {"create_array": [
                        {"create_struct": [
                            {"name": "hrs", "value": {"literal": " 00:00:00 UTC"}},
                            {
                                "name": "dt_range",
                                "value": {"generate_date_array": [
                                    {"literal": "2016-01-01"},
                                    {"current_date": {}},
                                    {"interval": [1, "day"]},
                                ]},
                            },
                        ]},
                        {"create_struct": [
                            {"name": "hrs", "value": {"literal": " 01:00:00 UTC"}},
                            {
                                "name": "dt_range",
                                "value": {"generate_date_array": [
                                    {"literal": "2016-01-01"},
                                    {"current_date": {}},
                                    {"interval": [1, "day"]},
                                ]},
                            },
                        ]},
                    ]},
                }},
            },
        }
        self.assertEqual(result, expected)

    def testH(self):
        sql = """
            SELECT
                -- [foo],
                ARRAY[foo],
                -- ARRAY<int64, STRING>[foo, bar],  INVALID
                ARRAY<STRING>[foo, bar],
                STRUCT(1, 3),
                STRUCT<int64, STRING>(2, 'foo')
            FROM
                T
            """
        result = parse(sql)
        expected = {
            "from": "T",
            "select": [
                {"value": {"create_array": "foo"}},
                {"value": {"cast": [{"create_array": ["foo", "bar"]}, {"array": {"string": {}}}]}},
                {"value": {"create_struct": [1, 3]}},
                {"value": {"cast": [
                    {"create_struct": [2, {"literal": "foo"}]},
                    {"struct": [{"int64": {}}, {"string": {}}]},
                ]}},
            ],
        }

        self.assertEqual(result, expected)

    def testK(self):
        sql = """
            SELECT
                STRUCT<int64, STRING>(2, 'foo')
            """
        result = parse(sql)
        expected = {"select": {"value": {"cast": [
            {"create_struct": [2, {"literal": "foo"}]},
            {"struct": [{"int64": {}}, {"string": {}}]},
        ]}}}

        self.assertEqual(result, expected)

    def testJ(self):
        sql = """
            SELECT
                current_date(),
                GENERATE_ARRAY(5, NULL, 1),
                GENERATE_DATE_ARRAY('2016-10-05', '2016-10-01', INTERVAL 1 DAY),
                GENERATE_DATE_ARRAY('2016-10-05', NULL),
                GENERATE_DATE_ARRAY('2016-01-01', '2016-12-31', INTERVAL 2 MONTH),
                GENERATE_DATE_ARRAY('2000-02-01',current_date(), INTERVAL 1 DAY),
                GENERATE_TIMESTAMP_ARRAY('2016-10-05 00:00:00', '2016-10-05 00:00:02', INTERVAL 1 SECOND)
            FROM
                bar
            """
        result = parse(sql)
        expected = {
            "from": "bar",
            "select": [
                {"value": {"current_date": {}}},
                {"value": {"generate_array": [5, {"null": {}}, 1]}},
                {"value": {"generate_date_array": [
                    {"literal": "2016-10-05"},
                    {"literal": "2016-10-01"},
                    {"interval": [1, "day"]},
                ]}},
                {"value": {"generate_date_array": [{"literal": "2016-10-05"}, {"null": {}}]}},
                {"value": {"generate_date_array": [
                    {"literal": "2016-01-01"},
                    {"literal": "2016-12-31"},
                    {"interval": [2, "month"]},
                ]}},
                {"value": {"generate_date_array": [
                    {"literal": "2000-02-01"},
                    {"current_date": {}},
                    {"interval": [1, "day"]},
                ]}},
                {"value": {"generate_timestamp_array": [
                    {"literal": "2016-10-05 00:00:00"},
                    {"literal": "2016-10-05 00:00:02"},
                    {"interval": [1, "second"]},
                ]}},
            ],
        }
        self.assertEqual(result, expected)

    def testN(self):
        sql = """
            SELECT DATE_SUB(current_date("-08:00"), INTERVAL 2 DAY)
            """
        result = parse(sql)
        expected = {"select": {"value": {"date_sub": [
            {"current_date": {"literal": "-08:00"}},
            {"interval": [2, "day"]},
        ]}}}
        self.assertEqual(result, expected)

    def testQ(self):
        sql = """
            WITH a AS (
                SELECT b FROM c
                UNION ALL
                (
                    WITH d AS (
                        SELECT e FROM f
                    )
                    SELECT g FROM d
                )
            )
            SELECT h FROM a
            """
        result = parse(sql)
        expected = {
            "from": "a",
            "select": {"value": "h"},
            "with": {
                "name": "a",
                "value": {"union_all": [
                    {"from": "c", "select": {"value": "b"}},
                    {
                        "from": "d",
                        "select": {"value": "g"},
                        "with": {"name": "d", "value": {"from": "f", "select": {"value": "e"}}},
                    },
                ]},
            },
        }
        self.assertEqual(result, expected)

    def testU(self):
        sql = """SELECT  * FROM `a`.b.`c`"""
        result = parse(sql)
        expected = {"from": "a.b.c", "select": "*"}
        self.assertEqual(result, expected)

    def testV(self):
        sql = """SELECT * FROM `a.b.c` a1
                JOIN `a.b.d` a2
                    ON cast(a1.field AS BIGDECIMAL) = cast(a2.field AS BIGNUMERIC)"""
        result = parse(sql)
        expected = {
            "select": "*",
            "from": [
                {"value": "a..b..c", "name": "a1"},
                {
                    "join": {"value": "a..b..d", "name": "a2"},
                    "on": {"eq": [
                        {"cast": ["a1.field", {"bigdecimal": {}}]},
                        {"cast": ["a2.field", {"bignumeric": {}}]},
                    ]},
                },
            ],
        }
        self.assertEqual(result, expected)

    def testW(self):
        sql = """SELECT * FROM `a.b.c` a1
                JOIN `a.b.d` a2
                    ON cast(a1.field AS INT64) = cast(a2.field AS BYTEINT)"""
        result = parse(sql)
        expected = {
            "select": "*",
            "from": [
                {"value": "a..b..c", "name": "a1"},
                {
                    "join": {"value": "a..b..d", "name": "a2"},
                    "on": {"eq": [{"cast": ["a1.field", {"int64": {}}]}, {"cast": ["a2.field", {"byteint": {}}]}]},
                },
            ],
        }
        self.assertEqual(result, expected)

    def testS(self):
        sql = """
            SELECT * FROM 'a'.b.`c`
            """
        with FuzzyTestCase.assertRaises("""'a'.b.`c`" (at char 27), (line:2, col:27)"""):
            parse(sql)

    def test_issue_96_r_expressions1(self):
        result = parse("SELECT regex_extract(x, r'[a-z]'), value FROM `a.b.c`")
        expected = {
            "from": "a..b..c",
            "select": [{"value": {"regex_extract": ["x", {"regex": "[a-z]"}]}}, {"value": "value"}],
        }
        self.assertEqual(result, expected)

    def test_issue_96_r_expressions2(self):
        result = parse('SELECT regex_extract(x, r"[a-z]"), value FROM `a.b.c`')
        expected = {
            "from": "a..b..c",
            "select": [{"value": {"regex_extract": ["x", {"regex": "[a-z]"}]}}, {"value": "value"}],
        }
        self.assertEqual(result, expected)

    def test_issue_97_safe_cast(self):
        result = parse("SELECT SAFE_CAST(x AS STRING) from `a.b.c`")
        expected = {
            "from": "a..b..c",
            "select": {"value": {"safe_cast": ["x", {"string": {}}]}},
        }
        self.assertEqual(result, expected)

    def test_issue_98_interval1(self):
        result = parse("""SELECT timestamp_add('2022-07-14T12:42:11Z', INTERVAL x MINUTE)""")
        expected = {"select": {"value": {"timestamp_add": [
            {"literal": "2022-07-14T12:42:11Z"},
            {"interval": ["x", "minute"]},
        ]}}}
        self.assertEqual(result, expected)

    @skip("missing FROM?")
    def test_issue_98_interval2(self):
        result = parse(
            """SELECT timestamp_add('2022-07-14T12:42:11Z', INTERVAL x MINUTE) UNNEST(GENERATE_ARRAY(1, 10)) as x"""
        )
        expected = {}
        self.assertEqual(result, expected)

    def test_issue_99_select_except(self):
        result = parse("SELECT * EXCEPT(x) FROM `a.b.c`")
        expected = {"from": "a..b..c", "select_except": {"value": "x"}}
        self.assertEqual(result, expected)

    def test_unnest(self):
        result = parse("""SELECT * FROM UNNEST([1, 2, 2, 5, NULL]) AS unnest_column WITH OFFSET AS `offset`""")
        expected = {
            "select": "*",
            "from": {
                "name": "unnest_column",
                "value": {"unnest": {"create_array": [1, 2, 2, 5, {"null": {}}]}},
                "with_offset": "offset",
            },
        }
        self.assertEqual(result, expected)

    def test_issue_123_declare1(self):
        sql = """DECLARE _current_timestamp timestamp DEFAULT current_timestamp();"""
        result = parse(sql)
        expected = {"declare": {
            "name": "_current_timestamp",
            "type": {"timestamp": {}},
            "default": {"current_timestamp": {}},
        }}
        self.assertEqual(result, expected)

    def test_issue_123_declare2(self):
        sql = """DECLARE _current_date      date      DEFAULT current_date("America/Sao_Paulo");"""
        result = parse(sql)
        expected = {"declare": {
            "name": "_current_date",
            "type": {"date": {}},
            "default": {"current_date": {"literal": "America/Sao_Paulo"}},
        }}
        self.assertEqual(result, expected)

    def test_issue_141_string_agg(self):
        sql = """
            SELECT 
                string_agg(address_type.name, ', ') as address_type_name
                ,string_agg(address.street order by length(address.street) limit 1) as street 
                ,string_agg(address.complement order by length(address.complement) limit 1) as complement 
        """
        result = parse(sql)
        expected = {"select": [
            {"name": "address_type_name", "value": {"string_agg": ["address_type.name", {"literal": ", "}]}},
            {
                "name": "street",
                "value": {
                    "limit": 1,
                    "orderby": {"value": {"length": "address.street"}},
                    "string_agg": "address.street",
                },
            },
            {
                "name": "complement",
                "value": {
                    "limit": 1,
                    "orderby": {"value": {"length": "address.complement"}},
                    "string_agg": "address.complement",
                },
            },
        ]}
        self.assertEqual(result, expected)

    def test_issue_142_array_agg(self):
        sql = """SELECT ARRAY_AGG(DISTINCT email IGNORE NULLS) AS email"""
        result = parse(sql)
        expect = {"select": {"name": "email", "value": {"array_agg": "email", "distinct": True, "nulls": "ignore"}}}
        self.assertEqual(result, expect)

    def test_issue_145(self):
        sql = """WITH
            shift_history_pivoted as (
                SELECT * FROM `*********************.**************.**************` 
                    UNPIVOT INCLUDE NULLS (
                        status FOR time_interval IN (
                            x0h00m_0h30m,
                            x0h30m_1h00m
                        )
                    )
            )            
            SELECT
                id
            FROM
                nu_com_a_mao_no_bolso
            WHERE
                time_interval IS NOT NULL
            """
        result = parse(sql)
        expected = {
            "select": {"value": "id"},
            "from": "nu_com_a_mao_no_bolso",
            "where": {"exists": "time_interval"},
            "with": {
                "name": "shift_history_pivoted",
                "value": {
                    "select": "*",
                    "from": "*********************..**************..**************",
                    "unpivot": {
                        "for": "time_interval",
                        "in": ["x0h00m_0h30m", "x0h30m_1h00m"],
                        "nulls": True,
                        "value": "status",
                    },
                },
            },
        }

        self.assertEqual(result, expected)

    def test_issue_150(self):
        sql = """SELECT AS STRUCT
            CASE
                WHEN ee.babala = TRUE THEN 'avisos'
                ELSE NULL
            END AS bot_name,
            ee.avisos AS estagio,
            SAFE_CAST(NULL AS STRING) AS demanda,
            SAFE_CAST(NULL AS STRING) AS transfere,
            SAFE_CAST(NULL AS STRING) AS segurana,
            SAFE_CAST(NULL AS BOOLEAN) AS jacson"""
        result = parse(sql)
        expected = {"select_as_struct": [
            {
                "name": "bot_name",
                "value": {"case": [
                    {"then": {"literal": "avisos"}, "when": {"eq": ["ee.babala", True]}},
                    {"null": {}},
                ]},
            },
            {"name": "estagio", "value": "ee.avisos"},
            {"name": "demanda", "value": {"safe_cast": [{"null": {}}, {"string": {}}]}},
            {"name": "transfere", "value": {"safe_cast": [{"null": {}}, {"string": {}}]}},
            {"name": "segurana", "value": {"safe_cast": [{"null": {}}, {"string": {}}]}},
            {"name": "jacson", "value": {"safe_cast": [{"null": {}}, {"boolean": {}}]}},
        ]}
        self.assertEqual(result, expected)

    def test_issue_155_trailing_comma(self):
        sql = """SELECT
            a.day AS src,
            b.day as tgt,
            ROW_NUMBER() OVER(PARTITION BY a.day ORDER BY b.day) - 1 AS qtde_wd,
        FROM workdays a
        join workdays b ON a.day <= b.day"""
        result = parse(sql)
        expected = {
            "from": [
                {"name": "a", "value": "workdays"},
                {"join": {"name": "b", "value": "workdays"}, "on": {"lte": ["a.day", "b.day"]}},
            ],
            "select": [
                {"name": "src", "value": "a.day"},
                {"name": "tgt", "value": "b.day"},
                {
                    "name": "qtde_wd",
                    "value": {"sub": [
                        {
                            "over": {"orderby": {"value": "b.day"}, "partitionby": "a.day"},
                            "value": {"row_number": {}},
                        },
                        1,
                    ]},
                },
            ],
        }
        self.assertEqual(result, expected)

    def test_issue_162_extract_from(self):
        result = parse(
            """SELECT
             FORMAT_DATETIME("%Y%m%d", DATETIME(full_date)) AS date_key,
             full_date, 
             FORMAT_DATETIME("%Y/%m/%d", DATETIME(full_date)) AS date_name,
             EXTRACT(dayofweek FROM full_date) AS day_of_week,
             CASE FORMAT_DATE('%A', date(full_date))
                 WHEN 'Sunday' THEN 'Domingo'
                 WHEN 'Monday' THEN 'Segunda-feira'
                 WHEN 'Tuesday' THEN 'Terça-feira'
                 WHEN 'Wednesday' THEN 'Quarta-feira'
                 WHEN 'Thursday' THEN 'Quinta-feira'
                 WHEN 'Friday' THEN 'Sexta-feira'
                 WHEN 'Saturday' THEN 'Sábado'
             END AS day_name_of_week,
             FORMAT_DATETIME("%d", DATETIME(full_date)) AS day_of_month,
             EXTRACT(dayofyear FROM full_date) AS day_of_year,
             CASE FORMAT_DATE('%A', DATE(full_date))
                 WHEN 'Saturday' THEN 'Final de Semana'
                 WHEN 'Sunday' THEN 'Final de Semana'
                 else 'Dia da Semana'
             END AS weekday_weekend,
             EXTRACT(week FROM full_date) + 1 AS week_of_year,
             CASE FORMAT_DATETIME("%B", DATETIME(full_date))
                 WHEN 'January' THEN 'Janeiro'
                 WHEN 'February' THEN 'Fevereiro'
                 WHEN 'March' THEN 'Março'
                 WHEN 'April' THEN 'Abril'
                 WHEN 'May' THEN 'Maio'
                 WHEN 'June' THEN 'Junho'
                 WHEN 'July' THEN 'Julho'
                 WHEN 'August' THEN 'Agosto'
                 WHEN 'September' THEN 'Setembro'
                 WHEN 'October' THEN 'Outubro'
                 WHEN 'November' THEN 'Novembro'
                 WHEN 'December' THEN 'Dezembro'
             END AS month_name,
             EXTRACT(month FROM full_date) AS month_of_year,
             IF(DATE_SUB(DATE_TRUNC(DATE_ADD(full_date, INTERVAL 1 MONTH), MONTH), INTERVAL 1 DAY) = full_date, 'Y', 'N') AS is_last_day_of_month,
             EXTRACT(quarter FROM full_date) AS calendar_quarter,
             EXTRACT(year FROM full_date) AS calendar_year,
             FORMAT_DATETIME("%Y-%m", DATETIME(full_date)) AS calendar_year_month,
             concat( EXTRACT(year FROM full_date), 'Q', EXTRACT(quarter FROM full_date)) AS calendar_year_qtr,
             20170921 AS insert_audit_key,
             20170921 AS update_audit_key,
             if(full_date = holiday.date, 1, 0) AS is_national_holiday,
             1 AS filter,
             DATE_SUB(DATE_TRUNC(DATE_ADD(full_date, INTERVAL 1 month), month), INTERVAL 1 DAY) AS last_day_of_month,
             FORMAT_DATETIME("%Y%m%d", DATETIME(DATE_SUB(DATE_TRUNC(DATE_ADD(full_date, INTERVAL 1 month), month), INTERVAL 1 DAY))) AS last_day_of_month_key,
             DATE_TRUNC(full_date, month) AS first_day_of_month,
             FORMAT_DATETIME("%Y%m%d", DATETIME(DATE_TRUNC(full_date, month))) AS first_day_of_month_key
        FROM UNNEST(GENERATE_DATE_ARRAY("2000-01-01", DATE_ADD(LAST_DAY(current_date, YEAR), INTERVAL 5 YEAR), INTERVAL 1 day)) AS full_date
        LEFT 
        JOIN financial_holiday holiday     
          ON holiday.date = full_date"""
        )
        expected = {
            "select": [
                {
                    "value": {"format_datetime": [{"literal": "%Y%m%d"}, {"datetime": "full_date"}]},
                    "name": "date_key",
                },
                {"value": "full_date"},
                {
                    "value": {"format_datetime": [{"literal": "%Y/%m/%d"}, {"datetime": "full_date"}]},
                    "name": "date_name",
                },
                {"value": {"extract": ["dow", "full_date"]}, "name": "day_of_week"},
                {
                    "value": {"case": [
                        {
                            "then": {"literal": "Domingo"},
                            "when": {"eq": [
                                {"format_date": [{"literal": "%A"}, {"date": "full_date"}]},
                                {"literal": "Sunday"},
                            ]},
                        },
                        {
                            "then": {"literal": "Segunda-feira"},
                            "when": {"eq": [
                                {"format_date": [{"literal": "%A"}, {"date": "full_date"}]},
                                {"literal": "Monday"},
                            ]},
                        },
                        {
                            "then": {"literal": "Terça-feira"},
                            "when": {"eq": [
                                {"format_date": [{"literal": "%A"}, {"date": "full_date"}]},
                                {"literal": "Tuesday"},
                            ]},
                        },
                        {
                            "then": {"literal": "Quarta-feira"},
                            "when": {"eq": [
                                {"format_date": [{"literal": "%A"}, {"date": "full_date"}]},
                                {"literal": "Wednesday"},
                            ]},
                        },
                        {
                            "then": {"literal": "Quinta-feira"},
                            "when": {"eq": [
                                {"format_date": [{"literal": "%A"}, {"date": "full_date"}]},
                                {"literal": "Thursday"},
                            ]},
                        },
                        {
                            "then": {"literal": "Sexta-feira"},
                            "when": {"eq": [
                                {"format_date": [{"literal": "%A"}, {"date": "full_date"}]},
                                {"literal": "Friday"},
                            ]},
                        },
                        {
                            "then": {"literal": "Sábado"},
                            "when": {"eq": [
                                {"format_date": [{"literal": "%A"}, {"date": "full_date"}]},
                                {"literal": "Saturday"},
                            ]},
                        },
                    ]},
                    "name": "day_name_of_week",
                },
                {
                    "value": {"format_datetime": [{"literal": "%d"}, {"datetime": "full_date"}]},
                    "name": "day_of_month",
                },
                {"value": {"extract": ["doy", "full_date"]}, "name": "day_of_year"},
                {
                    "value": {"case": [
                        {
                            "then": {"literal": "Final de Semana"},
                            "when": {"eq": [
                                {"format_date": [{"literal": "%A"}, {"date": "full_date"}]},
                                {"literal": "Saturday"},
                            ]},
                        },
                        {
                            "then": {"literal": "Final de Semana"},
                            "when": {"eq": [
                                {"format_date": [{"literal": "%A"}, {"date": "full_date"}]},
                                {"literal": "Sunday"},
                            ]},
                        },
                        {"literal": "Dia da Semana"},
                    ]},
                    "name": "weekday_weekend",
                },
                {"value": {"add": [{"extract": ["week", "full_date"]}, 1]}, "name": "week_of_year"},
                {
                    "value": {"case": [
                        {
                            "then": {"literal": "Janeiro"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "January"},
                            ]},
                        },
                        {
                            "then": {"literal": "Fevereiro"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "February"},
                            ]},
                        },
                        {
                            "then": {"literal": "Março"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "March"},
                            ]},
                        },
                        {
                            "then": {"literal": "Abril"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "April"},
                            ]},
                        },
                        {
                            "then": {"literal": "Maio"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "May"},
                            ]},
                        },
                        {
                            "then": {"literal": "Junho"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "June"},
                            ]},
                        },
                        {
                            "then": {"literal": "Julho"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "July"},
                            ]},
                        },
                        {
                            "then": {"literal": "Agosto"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "August"},
                            ]},
                        },
                        {
                            "then": {"literal": "Setembro"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "September"},
                            ]},
                        },
                        {
                            "then": {"literal": "Outubro"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "October"},
                            ]},
                        },
                        {
                            "then": {"literal": "Novembro"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "November"},
                            ]},
                        },
                        {
                            "then": {"literal": "Dezembro"},
                            "when": {"eq": [
                                {"format_datetime": [{"literal": "%B"}, {"datetime": "full_date"}]},
                                {"literal": "December"},
                            ]},
                        },
                    ]},
                    "name": "month_name",
                },
                {"value": {"extract": ["month", "full_date"]}, "name": "month_of_year"},
                {
                    "value": {"if": [
                        {"eq": [
                            {"date_sub": [
                                {"date_trunc": [{"date_add": ["full_date", {"interval": [1, "month"]}]}, "MONTH"]},
                                {"interval": [1, "day"]},
                            ]},
                            "full_date",
                        ]},
                        {"literal": "Y"},
                        {"literal": "N"},
                    ]},
                    "name": "is_last_day_of_month",
                },
                {"value": {"extract": ["quarter", "full_date"]}, "name": "calendar_quarter"},
                {"value": {"extract": ["year", "full_date"]}, "name": "calendar_year"},
                {
                    "value": {"format_datetime": [{"literal": "%Y-%m"}, {"datetime": "full_date"}]},
                    "name": "calendar_year_month",
                },
                {
                    "value": {"concat": [
                        {"extract": ["year", "full_date"]},
                        {"literal": "Q"},
                        {"extract": ["quarter", "full_date"]},
                    ]},
                    "name": "calendar_year_qtr",
                },
                {"value": 20170921, "name": "insert_audit_key"},
                {"value": 20170921, "name": "update_audit_key"},
                {"value": {"if": [{"eq": ["full_date", "holiday.date"]}, 1, 0]}, "name": "is_national_holiday"},
                {"value": 1, "name": "filter"},
                {
                    "value": {"date_sub": [
                        {"date_trunc": [{"date_add": ["full_date", {"interval": [1, "month"]}]}, "month"]},
                        {"interval": [1, "day"]},
                    ]},
                    "name": "last_day_of_month",
                },
                {
                    "value": {"format_datetime": [
                        {"literal": "%Y%m%d"},
                        {"datetime": {"date_sub": [
                            {"date_trunc": [{"date_add": ["full_date", {"interval": [1, "month"]}]}, "month"]},
                            {"interval": [1, "day"]},
                        ]}},
                    ]},
                    "name": "last_day_of_month_key",
                },
                {"value": {"date_trunc": ["full_date", "month"]}, "name": "first_day_of_month"},
                {
                    "value": {"format_datetime": [
                        {"literal": "%Y%m%d"},
                        {"datetime": {"date_trunc": ["full_date", "month"]}},
                    ]},
                    "name": "first_day_of_month_key",
                },
            ],
            "from": [
                {
                    "value": {"unnest": {"generate_date_array": [
                        {"literal": "2000-01-01"},
                        {"date_add": [{"last_day": ["current_date", "YEAR"]}, {"interval": [5, "year"]}]},
                        {"interval": [1, "day"]},
                    ]}},
                    "name": "full_date",
                },
                {
                    "left join": {"value": "financial_holiday", "name": "holiday"},
                    "on": {"eq": ["holiday.date", "full_date"]},
                },
            ],
        }
        self.assertEqual(result, expected)

    def test_issue_163_at_time_zone(self):
        result = parse(
            """
        SELECT
            REPLACE(CAST(EXTRACT(date from last_modified_date at time zone 'America/Sao_Paulo') AS STRING),'-','') as last_modified_date
        FROM
            territory2"""
        )
        expected = {
            "from": "territory2",
            "select": {
                "name": "last_modified_date",
                "value": {"replace": [
                    {"cast": [
                        {"extract": [
                            "date",
                            {"at_time_zone": ["last_modified_date", {"literal": "America/Sao_Paulo"}]},
                        ]},
                        {"string": {}},
                    ]},
                    {"literal": "-"},
                    {"literal": ""},
                ]},
            },
        }

        self.assertEqual(result, expected)

    def test_issue_164_at_time_zone2(self):
        result = parse(
            """
        SELECT
            REPLACE(
                cast(
                    extract(
                        date
                        FROM
                            last_login_date AT TIME ZONE 'America/Sao_Paulo'
                    ) AS STRING
                ),
                '-',
                ''
            ) AS last_login_date,
            REPLACE(
                cast(
                    extract(
                        date
                        FROM
                            last_modified_date AT TIME ZONE 'America/Sao_Paulo'
                    ) AS STRING
                ),
                '-',
                ''
            ) AS last_modified_date,
            REPLACE(
                cast(
                    extract(
                        date
                        FROM
                            last_viewed_date AT TIME ZONE 'America/Sao_Paulo'
                    ) AS STRING
                ),
                '-',
                ''
            ) AS last_viewed_date,
        FROM
            user u
        """
        )
        expected = {
            "from": {"name": "u", "value": "user"},
            "select": [
                {
                    "name": "last_login_date",
                    "value": {"replace": [
                        {"cast": [
                            {"extract": [
                                "date",
                                {"at_time_zone": ["last_login_date", {"literal": "America/Sao_Paulo"}]},
                            ]},
                            {"string": {}},
                        ]},
                        {"literal": "-"},
                        {"literal": ""},
                    ]},
                },
                {
                    "name": "last_modified_date",
                    "value": {"replace": [
                        {"cast": [
                            {"extract": [
                                "date",
                                {"at_time_zone": ["last_modified_date", {"literal": "America/Sao_Paulo"}]},
                            ]},
                            {"string": {}},
                        ]},
                        {"literal": "-"},
                        {"literal": ""},
                    ]},
                },
                {
                    "name": "last_viewed_date",
                    "value": {"replace": [
                        {"cast": [
                            {"extract": [
                                "date",
                                {"at_time_zone": ["last_viewed_date", {"literal": "America/Sao_Paulo"}]},
                            ]},
                            {"string": {}},
                        ]},
                        {"literal": "-"},
                        {"literal": ""},
                    ]},
                },
            ],
        }

        self.assertEqual(result, expected)

    def test_issue_165_select_as(self):
        result = parse(
            """
        SELECT
           ee.a_id AS id,
           CASE
            WHEN ee._id = 'flow2222222222222' THEN 'flow 2'
            WHEN ee._id = 'flow1111111111111' THEN 'flow 1'
            ELSE NULL
            END AS flow_name,
            array(
                SELECT AS STRUCT CASE
                                WHEN ee.step_started = TRUE THEN 'avisos'ELSE NULL END AS step_name,
                                ee.ws_status AS ws_status,
                                UNION ALL
                                SELECT AS STRUCT CASE
                                WHEN ee.dg_step_started = TRUE THEN 'dg' ELSE NULL END AS dg_step,
                                ee.dg_status AS dg_status,
                                CASE
                                WHEN cf.demand_informed = TRUE THEN 'informed'
                                WHEN cf.demand_informed = FALSE THEN ' not informed' ELSE NULL END AS description,
                                CASE WHEN cf.verification = TRUE THEN TRUE
                                WHEN cf.verification = FALSE THEN TRUE
                                WHEN cf.contact = TRUE THEN TRUE
                                WHEN cf.verification_sent = FALSE THEN FALSE ELSE NULL END AS verification_sent,
                                UNION ALL SELECT AS STRUCT
                                CASE WHEN ee.df_step = TRUE THEN 'test_df' ELSE NULL END AS df_step,
                                ee.df_status AS df_status,
                                SAFE_CAST (NULL AS STRING) AS team,
                                UNION ALL SELECT AS STRUCT
                                CASE WHEN ee.ir_step = TRUE THEN 'test_ir' ELSE NULL END AS ir_step,
                                ee.ir_status AS ir_status,
                                SAFE_CAST (NULL AS STRING) AS team2,
                                verification_sent) AS info,
             COALESCE (ee.email, ee.engagement_email) AS email,
             ee.synced_at
        FROM `project_id.dataset.table_name_a` ee
        LEFT JOIN `project_id.dataset.table_name_b` cf
             ON cf.b_id = ee.a_id
        WHERE ee._id <> 'flow333333333'
        AND (ee.team_name <> 'temp' OR ee.team_name IS NULL)
        """
        )
        expected = {
            "select": [
                {"name": "id", "value": "ee.a_id"},
                {
                    "name": "flow_name",
                    "value": {"case": [
                        {"then": {"literal": "flow 2"}, "when": {"eq": ["ee._id", {"literal": "flow2222222222222"}]},},
                        {"then": {"literal": "flow 1"}, "when": {"eq": ["ee._id", {"literal": "flow1111111111111"}]},},
                        {"null": {}},
                    ]},
                },
                {
                    "name": "info",
                    "value": {"create_array": {"union_all": [
                        {"select_as_struct": [
                            {
                                "name": "step_name",
                                "value": {"case": [
                                    {"then": {"literal": "avisos"}, "when": {"eq": ["ee.step_started", True]}},
                                    {"null": {}},
                                ]},
                            },
                            {"name": "ws_status", "value": "ee.ws_status"},
                        ]},
                        {"select_as_struct": [
                            {
                                "name": "dg_step",
                                "value": {"case": [
                                    {"then": {"literal": "dg"}, "when": {"eq": ["ee.dg_step_started", True]}},
                                    {"null": {}},
                                ]},
                            },
                            {"name": "dg_status", "value": "ee.dg_status"},
                            {
                                "name": "description",
                                "value": {"case": [
                                    {"then": {"literal": "informed"}, "when": {"eq": ["cf.demand_informed", True]}},
                                    {
                                        "then": {"literal": " not informed"},
                                        "when": {"eq": ["cf.demand_informed", False]},
                                    },
                                    {"null": {}},
                                ]},
                            },
                            {
                                "name": "verification_sent",
                                "value": {"case": [
                                    {"then": True, "when": {"eq": ["cf.verification", True]}},
                                    {"then": True, "when": {"eq": ["cf.verification", False]}},
                                    {"then": True, "when": {"eq": ["cf.contact", True]}},
                                    {"then": False, "when": {"eq": ["cf.verification_sent", False]}},
                                    {"null": {}},
                                ]},
                            },
                        ]},
                        {"select_as_struct": [
                            {
                                "name": "df_step",
                                "value": {"case": [
                                    {"then": {"literal": "test_df"}, "when": {"eq": ["ee.df_step", True]}},
                                    {"null": {}},
                                ]},
                            },
                            {"name": "df_status", "value": "ee.df_status"},
                            {"name": "team", "value": {"safe_cast": [{"null": {}}, {"string": {}}]}},
                        ]},
                        {"select_as_struct": [
                            {
                                "name": "ir_step",
                                "value": {"case": [
                                    {"then": {"literal": "test_ir"}, "when": {"eq": ["ee.ir_step", True]}},
                                    {"null": {}},
                                ]},
                            },
                            {"name": "ir_status", "value": "ee.ir_status"},
                            {"name": "team2", "value": {"safe_cast": [{"null": {}}, {"string": {}}]}},
                            {"value": "verification_sent"},
                        ]},
                    ]}},
                },
                {"name": "email", "value": {"coalesce": ["ee.email", "ee.engagement_email"]}},
                {"value": "ee.synced_at"},
            ],
            "from": [
                {"name": "ee", "value": "project_id..dataset..table_name_a"},
                {
                    "left join": {"name": "cf", "value": "project_id..dataset..table_name_b"},
                    "on": {"eq": ["cf.b_id", "ee.a_id"]},
                },
            ],
            "where": {"and": [
                {"neq": ["ee._id", {"literal": "flow333333333"}]},
                {"or": [{"neq": ["ee.team_name", {"literal": "temp"}]}, {"missing": "ee.team_name"}]},
            ]},
        }
        self.assertEqual(result, expected)
        #         WHERE ee._id <> 'flow333333333'
        #         AND (ee.team_name <> 'temp' OR ee.team_name IS NULL)

    def test_issue_165_select_as2(self):
        result = parse(
            """
        SELECT
            array(
                SELECT AS STRUCT 
                    CASE WHEN ee.step_started = TRUE THEN 'avisos'ELSE NULL END AS step_name,
                    ee.ws_status AS ws_status,
                UNION ALL
                SELECT AS STRUCT 
                    value1 AS a,
                    value2 AS b,
                    value3 AS c,
            ) AS info,
        FROM ee
        """
        )
        expected = {
            "from": "ee",
            "select": {
                "name": "info",
                "value": {"create_array": {"union_all": [
                    {"select_as_struct": [
                        {
                            "name": "step_name",
                            "value": {"case": [
                                {"then": {"literal": "avisos"}, "when": {"eq": ["ee.step_started", True]}},
                                {"null": {}},
                            ]},
                        },
                        {"name": "ws_status", "value": "ee.ws_status"},
                    ]},
                    {"select_as_struct": [
                        {"name": "a", "value": "value1"},
                        {"name": "b", "value": "value2"},
                        {"name": "c", "value": "value3"},
                    ]},
                ]}},
            },
        }

        self.assertEqual(result, expected)

    def test_issue_172_window1(self):
        # https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax#qualify_clause
        result = parse(
            """
        SELECT * 
        FROM first_stage
        QUALIFY (agent_in AND IFNULL(LAG(agent_in) OVER win, FALSE)) = FALSE 
        WINDOW win AS (PARTITION BY id ORDER BY event_created_at)
        """
        )
        expected = {
            "from": "first_stage",
            "qualify": {"eq": [
                {"and": ["agent_in", {"ifnull": [{"over": "win", "value": {"lag": "agent_in"}}, False]}]},
                False,
            ]},
            "select": "*",
            "window": {"name": "win", "value": {"orderby": {"value": "event_created_at"}, "partitionby": "id"}},
        }
        self.assertEqual(result, expected)

    def test_issue_172_window2(self):
        sql = """
        with first_stage AS (
          SELECT
            id,
            created_at,
            event_created_at,
            message IN ('test1', 'test2') AS agent_out,
            message IN ('test3','test4','test5') AS agent_in,
          FROM
            project.dataset.table
          WHERE
            message IN (
              'test1',
              'test2',
              'test3',
              'test4',
              'test5'
            )
        ),
        
        second_stage AS (
          SELECT
            id,
            created_at,
            event_created_at AS queue_start_at,
            agent_in,
            CASE
            WHEN LEAD(agent_out) OVER win = TRUE THEN LEAD(event_created_at) OVER win
            WHEN agent_out THEN NULL
            ELSE IFNULL(
            DATETIME_SUB(LEAD(event_created_at) OVER win,INTERVAL 1 MILLISECOND),DATETIME('9999-12-30'))
            END AS queue_end_at,
          FROM
            (
              SELECT * FROM first_stage
              QUALIFY (agent_in AND IFNULL(LAG(agent_in) OVER win, FALSE)) = FALSE 
              WINDOW win AS (
                  PARTITION BY id
                  ORDER BY
                  event_created_at
              )
            )
            WINDOW win AS (
              PARTITION BY id
              ORDER BY
              event_created_at
            )
        )
        select * from second_stage"""
        result = parse(sql)
        expected = {
            "with": [
                {
                    "name": "first_stage",
                    "value": {
                        "select": [
                            {"value": "id"},
                            {"value": "created_at"},
                            {"value": "event_created_at"},
                            {"name": "agent_out", "value": {"in": ["message", {"literal": ["test1", "test2"]}]}},
                            {
                                "name": "agent_in",
                                "value": {"in": ["message", {"literal": ["test3", "test4", "test5"]}]},
                            },
                        ],
                        "from": "project.dataset.table",
                        "where": {"in": ["message", {"literal": ["test1", "test2", "test3", "test4", "test5"]}]},
                    },
                },
                {
                    "name": "second_stage",
                    "value": {
                        "select": [
                            {"value": "id"},
                            {"value": "created_at"},
                            {"name": "queue_start_at", "value": "event_created_at"},
                            {"value": "agent_in"},
                            {
                                "name": "queue_end_at",
                                "value": {"case": [
                                    {
                                        "then": {"over": "win", "value": {"lead": "event_created_at"}},
                                        "when": {"eq": [{"over": "win", "value": {"lead": "agent_out"}}, True]},
                                    },
                                    {"then": {"null": {}}, "when": "agent_out"},
                                    {"ifnull": [
                                        {"datetime_sub": [
                                            {"over": "win", "value": {"lead": "event_created_at"}},
                                            {"interval": [1, "millisecond"]},
                                        ]},
                                        {"datetime": {"literal": "9999-12-30"}},
                                    ]},
                                ]},
                            },
                        ],
                        "from": {
                            "select": "*",
                            "from": "first_stage",
                            "qualify": {"eq": [
                                {"and": [
                                    "agent_in",
                                    {"ifnull": [{"over": "win", "value": {"lag": "agent_in"}}, False]},
                                ]},
                                False,
                            ]},
                            "window": {
                                "name": "win",
                                "value": {"orderby": {"value": "event_created_at"}, "partitionby": "id"},
                            },
                        },
                        "window": {
                            "name": "win",
                            "value": {"orderby": {"value": "event_created_at"}, "partitionby": "id"},
                        },
                    },
                },
            ],
            "select": "*",
            "from": "second_stage",
        }
        self.assertEqual(result, expected)

    def test_issue_182_pivot_w_name(self):
        sql = """SELECT * from (
              SELECT
                rt.projectId,
                rt.datasetId,
                rt.tableId,
                count(distinct rt.jobId) jobs
              FROM
                `project.dataset.table_test` rt
              Group by 1,2,3,4
            
            ) PIVOT (
              sum(jobs) as jobs
              for statementType in (
                'BEGIN_TRANSACTION'
                , 'SCRIPT'
                , 'MERGE'
                , 'CREATE_TABLE_AS_SELECT'
                , 'UPDATE'
                , 'SELECT'
                , 'TRUNCATE_TABLE'
                , 'DELETE'
                , 'CREATE_VIEW'
                , 'DROP_VIEW'
                , 'DROP_TABLE'
                , 'COMMIT_TRANSACTION'
                , 'INSERT'
                , 'CREATE_TABLE_FUNCTION'
                , 'ASSERT'
                , 'CREATE_FUNCTION'
                , 'QUERY_STATEMENT_TYPE_UNSPECIFIED'
                , 'ALTER_TABLE'
                , 'CREATE_TABLE'
              )
            )"""
        result = parse(sql)
        expected = {
            "select": "*",
            "from": {
                "select": [
                    {"value": "rt.projectId"},
                    {"value": "rt.datasetId"},
                    {"value": "rt.tableId"},
                    {"name": "jobs", "value": {"count": "rt.jobId", "distinct": True}},
                ],
                "from": {"name": "rt", "value": "project..dataset..table_test"},
                "groupby": [{"value": 1}, {"value": 2}, {"value": 3}, {"value": 4}],
            },
            "pivot": {
                "aggregate": {"name": "jobs", "value": {"sum": "jobs"}},
                "for": "statementType",
                "in": {"literal": [
                    "BEGIN_TRANSACTION",
                    "SCRIPT",
                    "MERGE",
                    "CREATE_TABLE_AS_SELECT",
                    "UPDATE",
                    "SELECT",
                    "TRUNCATE_TABLE",
                    "DELETE",
                    "CREATE_VIEW",
                    "DROP_VIEW",
                    "DROP_TABLE",
                    "COMMIT_TRANSACTION",
                    "INSERT",
                    "CREATE_TABLE_FUNCTION",
                    "ASSERT",
                    "CREATE_FUNCTION",
                    "QUERY_STATEMENT_TYPE_UNSPECIFIED",
                    "ALTER_TABLE",
                    "CREATE_TABLE",
                ]},
            },
        }

        self.assertEqual(result, expected)

    def test_issue_205(self):
        sql = """select CAST(date(2023,1,1) AS STRING FORMAT 'YYYY-MM') AS year_month"""
        result = parse(sql)
        expected = {"select": {
            "name": "year_month",
            "value": {"cast": [{"date": [2023, 1, 1]}, {"string_format": {"literal": "YYYY-MM"}}]},
        }}

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

    def test_issue_207(self):
        query = """select struct('a' as col1) as cc"""
        result = parse(query)
        expected = {"select": {"name": "cc", "value": {"create_struct": {"name": "col1", "value": {"literal": "a"}}}}}
        self.assertEqual(result, expected)

    def test_issue_208(self):
        # https://cloud.google.com/bigquery/docs/access-historical-data#query_data_at_a_point_in_time
        sql = """SELECT *
        FROM `mydataset.mytable`
          FOR SYSTEM_TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);
        """
        result = parse(sql)
        expected = {
            "from": {
                "for_system_time_as_of": {"timestamp_sub": [{"current_timestamp": {}}, {"interval": [1, "hour"]}]},
                "value": "mydataset..mytable",
            },
            "select": "*",
        }
        self.assertEqual(result, expected)

    def test_issue_210(self):
        # https://cloud.google.com/bigquery/docs/access-historical-data#query_data_at_a_point_in_time
        sql = """SELECT *
        FROM `mydataset.mytable`
          FOR SYSTEM TIME AS OF TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR);
        """
        result = parse(sql)
        expected = {
            "from": {
                "for_system_time_as_of": {"timestamp_sub": [{"current_timestamp": {}}, {"interval": [1, "hour"]}]},
                "value": "mydataset..mytable",
            },
            "select": "*",
        }
        self.assertEqual(result, expected)

    @skip("not ready yet")
    def test_issue_214(self):
        sql = """
            select 
                raw_data.* except(col3),
                col3 + col1 as new_col
            from raw_data
        """
        result = parse(sql)
        expected = {
            "from": "raw_data",
            "select": [
                {"all_columns": {"from": "raw_data"}, "except": "col3"},
                {"name": "new_col", "value": {"add": ["col3", "col1"]}},
            ],
        }
        self.assertEqual(result, expected)

    @skip("not ready yet")
    def test_issue_215(self):
        sql = """
            select 
                col3 + col1 as new_col,
                * except(col3)
            from raw_data
        """
        result = parse(sql)
        expected = {
            "from": "raw_data",
            "select": [{"name": "new_col", "value": {"add": ["col3", "col1"]}}, {"all_columns": {}, "except": "col3"}],
        }
        self.assertEqual(result, expected)

    def test_issue_216(self):
        sql = """
            with raw_data as (
            select 
                    * 
            from UNNEST(GENERATE_ARRAY(1, 2)) as col1
            ),
            raw_data2 as (
            select 
            *, 
            1 as cn1, 
            2 as cn2, 
            from UNNEST(GENERATE_ARRAY(1, 2)) as col2
            )
            select 
                *
            from raw_data
            left join raw_data2 on raw_data.col1 = raw_data2.col2, unnest ([raw_data2.cn1, raw_data2.cn2]) as unnested_res
        """
        result = parse(sql)
        expected = {
            "from": [
                "raw_data",
                {"left join": "raw_data2", "on": {"eq": ["raw_data.col1", "raw_data2.col2"]}},
                {"cross join": {
                    "name": "unnested_res",
                    "value": {"unnest": {"create_array": ["raw_data2.cn1", "raw_data2.cn2"]}},
                }},
            ],
            "select": "*",
            "with": [
                {
                    "name": "raw_data",
                    "value": {
                        "from": {"name": "col1", "value": {"unnest": {"generate_array": [1, 2]}}},
                        "select": "*",
                    },
                },
                {
                    "name": "raw_data2",
                    "value": {
                        "from": {"name": "col2", "value": {"unnest": {"generate_array": [1, 2]}}},
                        "select": ["*", {"name": "cn1", "value": 1}, {"name": "cn2", "value": 2}],
                    },
                },
            ],
        }
        self.assertEqual(result, expected)

    def test_issue_216b(self):
        sql = """
            select 
                *
            from raw_data
            left join raw_data2 as b on raw_data.col1 = b.col2, unnest ([raw_data2.cn1, raw_data2.cn2]) as unnested_res
        """
        result = parse(sql)
        expected = {
            "from": [
                "raw_data",
                {"left join": {"name": "b", "value": "raw_data2"}, "on": {"eq": ["raw_data.col1", "b.col2"]}},
                {"cross join": {
                    "name": "unnested_res",
                    "value": {"unnest": {"create_array": ["raw_data2.cn1", "raw_data2.cn2"]}},
                }},
            ],
            "select": "*",
        }
        self.assertEqual(result, expected)
        new_sql = format(result)
        self.assertEqual(
            new_sql,
            """SELECT * FROM raw_data LEFT JOIN raw_data2 AS b ON raw_data.col1 = b.col2 CROSS JOIN UNNEST([raw_data2.cn1, raw_data2.cn2]) AS unnested_res""",
        )

    def test_issue_224(self):
        sql = """
        WITH Produce AS (
          SELECT 'Kale' as product, 51 as sales, 'Q1' as quarter, 2020 as year UNION ALL
          SELECT 'Kale', 23, 'Q2', 2020 UNION ALL
          SELECT 'Kale', 45, 'Q3', 2020 UNION ALL
          SELECT 'Kale', 3, 'Q4', 2020 UNION ALL
          SELECT 'Kale', 70, 'Q1', 2021 UNION ALL
          SELECT 'Kale', 85, 'Q2', 2021 UNION ALL
          SELECT 'Apple', 77, 'Q1', 2020 UNION ALL
          SELECT 'Apple', 0, 'Q2', 2020 UNION ALL
          SELECT 'Apple', 1, 'Q1', 2021
          )
        SELECT * FROM Produce
        PIVOT(
          max(sales) as max_sales, 
          min(sales) as min_sales
          FOR quarter IN ('Q1', 'Q2','Q3', 'Q4')
          );"""
        result = parse(sql)
        expected = {
            "from": "Produce",
            "pivot": {
                "aggregate": [
                    {"value": {"max": "sales"}, "name": "max_sales"},
                    {"value": {"min": "sales"}, "name": "min_sales"},
                ],
                "for": "quarter",
                "in": {"literal": ["Q1", "Q2", "Q3", "Q4"]},
            },
            "select": "*",
            "with": {
                "name": "Produce",
                "value": {"union_all": [
                    {"select": [
                        {"name": "product", "value": {"literal": "Kale"}},
                        {"name": "sales", "value": 51},
                        {"name": "quarter", "value": {"literal": "Q1"}},
                        {"name": "year", "value": 2020},
                    ]},
                    {"select": [
                        {"value": {"literal": "Kale"}},
                        {"value": 23},
                        {"value": {"literal": "Q2"}},
                        {"value": 2020},
                    ]},
                    {"select": [
                        {"value": {"literal": "Kale"}},
                        {"value": 45},
                        {"value": {"literal": "Q3"}},
                        {"value": 2020},
                    ]},
                    {"select": [
                        {"value": {"literal": "Kale"}},
                        {"value": 3},
                        {"value": {"literal": "Q4"}},
                        {"value": 2020},
                    ]},
                    {"select": [
                        {"value": {"literal": "Kale"}},
                        {"value": 70},
                        {"value": {"literal": "Q1"}},
                        {"value": 2021},
                    ]},
                    {"select": [
                        {"value": {"literal": "Kale"}},
                        {"value": 85},
                        {"value": {"literal": "Q2"}},
                        {"value": 2021},
                    ]},
                    {"select": [
                        {"value": {"literal": "Apple"}},
                        {"value": 77},
                        {"value": {"literal": "Q1"}},
                        {"value": 2020},
                    ]},
                    {"select": [
                        {"value": {"literal": "Apple"}},
                        {"value": 0},
                        {"value": {"literal": "Q2"}},
                        {"value": 2020},
                    ]},
                    {"select": [
                        {"value": {"literal": "Apple"}},
                        {"value": 1},
                        {"value": {"literal": "Q1"}},
                        {"value": 2021},
                    ]},
                ]},
            },
        }

        self.assertEqual(result, expected)

    def test_issue_227_name(self):
        query = """ select * from proj-prd.dataset.table"""
        result = parse(query)
        expected = {"from": "proj-prd.dataset.table", "select": "*"}
        self.assertEqual(result, expected)

    def test_issue_242_stack_overflow_2(self):
        query = """
        SELECT (FORMAT_TIMESTAMP('%Y-%m', analytics.event_timestamp, 'Region/TimeZone')) AS event_timestamp_month,  
        COUNT(DISTINCT CASE  WHEN (engagements.engagement_segment = 'engaged')  
        THEN engagements.user_id ELSE NULL END) AS engagements_engaged_user  
        FROM "database"."schema"."analytics" AS analytics  
        LEFT JOIN "database"."schema"."content" AS content  
        ON analytics.content_id = content.id  
        AND analytics.site = content.site  
        LEFT JOIN UNNEST(content.matching_teams) AS _q_0(content_matching_teams)  
        LEFT JOIN "database"."schema"."engagements" AS engagements  
        ON (DATE(analytics.event_timestamp, 'Region/TimeZone')) = engagements.event_date  
        AND analytics.user_id = engagements.user_id  
        AND (engagements.event_date BETWEEN  (DATE(COALESCE(TIMESTAMP(DATETIME_ADD(DATETIME(TIMESTAMP_TRUNC(TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), DAY, 'Region/TimeZone'), MONTH, 'Region/TimeZone'), 'Region/TimeZone'), -6, MONTH), 'Region/TimeZone'), CURRENT_TIMESTAMP()), 'Region/TimeZone'))  
        AND (DATE(COALESCE(TIMESTAMP(DATETIME_ADD(DATETIME(TIMESTAMP(DATETIME_ADD(DATETIME(TIMESTAMP_TRUNC(TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), DAY, 'Region/TimeZone'), MONTH, 'Region/TimeZone'), 'Region/TimeZone'), -6, MONTH), 'Region/TimeZone'), 'Region/TimeZone'), 6, MONTH), 'Region/TimeZone'), CURRENT_TIMESTAMP()), 'Region/TimeZone')))  
        WHERE ((REGEXP_EXTRACT(analytics.event_params__page_location, '^https?:\\/\\/(?:www\\.)?([^\\/]+)', 1)) IS NULL  
        OR (REGEXP_EXTRACT(analytics.event_params__page_location, '^https?:\\/\\/(?:www\\.)?([^\\/]+)', 1)) = 'example1.com'  
        OR (REGEXP_EXTRACT(analytics.event_params__page_location, '^https?:\\/\\/(?:www\\.)?([^\\/]+)', 1)) = 'example2.com'  
        OR (REGEXP_EXTRACT(analytics.event_params__page_location, '^https?:\\/\\/(?:www\\.)?([^\\/]+)', 1)) = 'example3.com'  
        OR (REGEXP_EXTRACT(analytics.event_params__page_location, '^https?:\\/\\/(?:www\\.)?([^\\/]+)', 1)) = 'example4.com')  
        AND (_q_0.content_matching_teams) = 'Team/Team (Gesamt)'  
        AND (((analytics.event_timestamp) >=  (TIMESTAMP(DATETIME_ADD(DATETIME(TIMESTAMP_TRUNC(TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), DAY, 'Region/TimeZone'), MONTH, 'Region/TimeZone'), 'Region/TimeZone'), -6, MONTH), 'Region/TimeZone')))  
        AND (analytics.event_timestamp) <  (TIMESTAMP(DATETIME_ADD(DATETIME(TIMESTAMP(DATETIME_ADD(DATETIME(TIMESTAMP_TRUNC(TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), DAY, 'Region/TimeZone'), MONTH, 'Region/TimeZone'), 'Region/TimeZone'), -6, MONTH), 'Region/TimeZone'), 'Region/TimeZone'), 6, MONTH), 'Region/TimeZone')))
        AND (analytics.site = 'X')  
        AND (analytics.site IN ('X'))  
        AND (1 = 1 AND _q_0.content_matching_teams LIKE 'Team/Team')  
        GROUP BY (FORMAT_TIMESTAMP('%Y-%m', analytics.event_timestamp, 'Region/TimeZone'))  
        ORDER BY event_timestamp_month DESC  LIMIT 500
        """
        result = parse(query)
        expected = {
            "from": [
                {"name": "analytics", "value": "database.schema.analytics"},
                {
                    "left join": {"name": "content", "value": "database.schema.content"},
                    "on": {"and": [
                        {"eq": ["analytics.content_id", "content.id"]},
                        {"eq": ["analytics.site", "content.site"]},
                    ]},
                },
                {"left join": {
                    "name": {"_q_0": "content_matching_teams"},
                    "value": {"unnest": "content.matching_teams"},
                }},
                {
                    "left join": {"name": "engagements", "value": "database.schema.engagements"},
                    "on": {"and": [
                        {"eq": [
                            {"date": ["analytics.event_timestamp", {"literal": "Region/TimeZone"}]},
                            "engagements.event_date",
                        ]},
                        {"eq": ["analytics.user_id", "engagements.user_id"]},
                        {"between": [
                            "engagements.event_date",
                            {"date": [
                                {"coalesce": [
                                    {"timestamp": [
                                        {"datetime_add": [
                                            {"datetime": [
                                                {"timestamp_trunc": [
                                                    {"timestamp_trunc": [
                                                        {"current_timestamp": {}},
                                                        "DAY",
                                                        {"literal": "Region/TimeZone"},
                                                    ]},
                                                    "MONTH",
                                                    {"literal": "Region/TimeZone"},
                                                ]},
                                                {"literal": "Region/TimeZone"},
                                            ]},
                                            -6,
                                            "MONTH",
                                        ]},
                                        {"literal": "Region/TimeZone"},
                                    ]},
                                    {"current_timestamp": {}},
                                ]},
                                {"literal": "Region/TimeZone"},
                            ]},
                            {"date": [
                                {"coalesce": [
                                    {"timestamp": [
                                        {"datetime_add": [
                                            {"datetime": [
                                                {"timestamp": [
                                                    {"datetime_add": [
                                                        {"datetime": [
                                                            {"timestamp_trunc": [
                                                                {"timestamp_trunc": [
                                                                    {"current_timestamp": {}},
                                                                    "DAY",
                                                                    {"literal": "Region/TimeZone"},
                                                                ]},
                                                                "MONTH",
                                                                {"literal": "Region/TimeZone"},
                                                            ]},
                                                            {"literal": "Region/TimeZone"},
                                                        ]},
                                                        -6,
                                                        "MONTH",
                                                    ]},
                                                    {"literal": "Region/TimeZone"},
                                                ]},
                                                {"literal": "Region/TimeZone"},
                                            ]},
                                            6,
                                            "MONTH",
                                        ]},
                                        {"literal": "Region/TimeZone"},
                                    ]},
                                    {"current_timestamp": {}},
                                ]},
                                {"literal": "Region/TimeZone"},
                            ]},
                        ]},
                    ]},
                },
            ],
            "groupby": {"value": {"format_timestamp": [
                {"literal": "%Y-%m"},
                "analytics.event_timestamp",
                {"literal": "Region/TimeZone"},
            ]}},
            "limit": 500,
            "orderby": {"sort": "desc", "value": "event_timestamp_month"},
            "select": [
                {
                    "name": "event_timestamp_month",
                    "value": {"format_timestamp": [
                        {"literal": "%Y-%m"},
                        "analytics.event_timestamp",
                        {"literal": "Region/TimeZone"},
                    ]},
                },
                {
                    "name": "engagements_engaged_user",
                    "value": {
                        "count": {"case": [
                            {
                                "then": "engagements.user_id",
                                "when": {"eq": ["engagements.engagement_segment", {"literal": "engaged"}]},
                            },
                            {"null": {}},
                        ]},
                        "distinct": True,
                    },
                },
            ],
            "where": {"and": [
                {"or": [
                    {"missing": {"regexp_extract": [
                        "analytics.event_params__page_location",
                        {"literal": "^https?:\\/\\/(?:www\\.)?([^\\/]+)"},
                        1,
                    ]}},
                    {"eq": [
                        {"regexp_extract": [
                            "analytics.event_params__page_location",
                            {"literal": "^https?:\\/\\/(?:www\\.)?([^\\/]+)"},
                            1,
                        ]},
                        {"literal": "example1.com"},
                    ]},
                    {"eq": [
                        {"regexp_extract": [
                            "analytics.event_params__page_location",
                            {"literal": "^https?:\\/\\/(?:www\\.)?([^\\/]+)"},
                            1,
                        ]},
                        {"literal": "example2.com"},
                    ]},
                    {"eq": [
                        {"regexp_extract": [
                            "analytics.event_params__page_location",
                            {"literal": "^https?:\\/\\/(?:www\\.)?([^\\/]+)"},
                            1,
                        ]},
                        {"literal": "example3.com"},
                    ]},
                    {"eq": [
                        {"regexp_extract": [
                            "analytics.event_params__page_location",
                            {"literal": "^https?:\\/\\/(?:www\\.)?([^\\/]+)"},
                            1,
                        ]},
                        {"literal": "example4.com"},
                    ]},
                ]},
                {"eq": ["_q_0.content_matching_teams", {"literal": "Team/Team (Gesamt)"}]},
                {"gte": [
                    "analytics.event_timestamp",
                    {"timestamp": [
                        {"datetime_add": [
                            {"datetime": [
                                {"timestamp_trunc": [
                                    {"timestamp_trunc": [
                                        {"current_timestamp": {}},
                                        "DAY",
                                        {"literal": "Region/TimeZone"},
                                    ]},
                                    "MONTH",
                                    {"literal": "Region/TimeZone"},
                                ]},
                                {"literal": "Region/TimeZone"},
                            ]},
                            -6,
                            "MONTH",
                        ]},
                        {"literal": "Region/TimeZone"},
                    ]},
                ]},
                {"lt": [
                    "analytics.event_timestamp",
                    {"timestamp": [
                        {"datetime_add": [
                            {"datetime": [
                                {"timestamp": [
                                    {"datetime_add": [
                                        {"datetime": [
                                            {"timestamp_trunc": [
                                                {"timestamp_trunc": [
                                                    {"current_timestamp": {}},
                                                    "DAY",
                                                    {"literal": "Region/TimeZone"},
                                                ]},
                                                "MONTH",
                                                {"literal": "Region/TimeZone"},
                                            ]},
                                            {"literal": "Region/TimeZone"},
                                        ]},
                                        -6,
                                        "MONTH",
                                    ]},
                                    {"literal": "Region/TimeZone"},
                                ]},
                                {"literal": "Region/TimeZone"},
                            ]},
                            6,
                            "MONTH",
                        ]},
                        {"literal": "Region/TimeZone"},
                    ]},
                ]},
                {"eq": ["analytics.site", {"literal": "X"}]},
                {"in": ["analytics.site", {"literal": "X"}]},
                {"eq": [1, 1]},
                {"like": ["_q_0.content_matching_teams", {"literal": "Team/Team"}]},
            ]},
        }

        self.assertEqual(result, expected)
