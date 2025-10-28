# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from itertools import zip_longest
from unittest import skip

from mo_files import File
from mo_testing.fuzzytestcase import add_error_reporting, FuzzyTestCase, assertAlmostEqual

from mo_sql_parsing import parse, parse_mysql, parse_delimiters


@add_error_reporting
class TestMySql(FuzzyTestCase):
    def test_issue_22(self):
        sql = 'SELECT "fred"'
        result = parse_mysql(sql)
        expected = {"select": {"value": {"literal": "fred"}}}
        self.assertEqual(result, expected)

    def test_issue_126(self):
        from mo_sql_parsing import parse_mysql as parse

        result = parse(
            """SELECT algid, item_id, avg(score) as avg_score 
            from (
                select 
                    ds, 
                    algid, 
                    uin, 
                    split(item_result, ":")[0] as item_id, 
                    split(item_result, ": ")[1] as score 
                from (
                    select ds, scorealgid_ as algid, uin_ as uin, item_result 
                    from (
                        select * 
                        from t_dwd_tmp_wxpay_discount_model_score_hour 
                        where ds >= 2022080300 and ds <= 2022080323
                    )day_tbl 
                    LATERAL VIEW explode(split(scoreresult_, "\\ | ")) temp AS item_result
                ) t
            ) tbl 
            group by algid, item_id;"""
        )
        expected = {
            "from": {
                "name": "tbl",
                "value": {
                    "from": {
                        "name": "t",
                        "value": {
                            "from": [
                                {
                                    "name": "day_tbl",
                                    "value": {
                                        "from": "t_dwd_tmp_wxpay_discount_model_score_hour",
                                        "select": {"all_columns": {}},
                                        "where": {"and": [{"gte": ["ds", 2022080300]}, {"lte": ["ds", 2022080323]}]},
                                    },
                                },
                                {"lateral view": {
                                    "name": {"temp": "item_result"},
                                    "value": {"explode": {"split": ["scoreresult_", {"literal": "\\ | "}]}},
                                }},
                            ],
                            "select": [
                                {"value": "ds"},
                                {"name": "algid", "value": "scorealgid_"},
                                {"name": "uin", "value": "uin_"},
                                {"value": "item_result"},
                            ],
                        },
                    },
                    "select": [
                        {"value": "ds"},
                        {"value": "algid"},
                        {"value": "uin"},
                        {"name": "item_id", "value": {"get": [{"split": ["item_result", {"literal": ":"}]}, 0]}},
                        {"name": "score", "value": {"get": [{"split": ["item_result", {"literal": ": "}]}, 1]}},
                    ],
                },
            },
            "groupby": [{"value": "algid"}, {"value": "item_id"}],
            "select": [{"value": "algid"}, {"value": "item_id"}, {"name": "avg_score", "value": {"avg": "score"}}],
        }
        self.assertEqual(result, expected)

    def test_issue_157_describe1(self):
        sql = """Explain format=traditional select * from temp"""
        result = parse(sql)
        expected = {"explain": {"from": "temp", "select": {"all_columns": {}}}, "format": "traditional"}
        self.assertEqual(result, expected)

    def test_issue_157_describe2(self):
        sql = """desc format=tree select * from temp"""
        result = parse(sql)
        expected = {"explain": {"from": "temp", "select": {"all_columns": {}}}, "format": "tree"}
        self.assertEqual(result, expected)

    def test_issue_157_describe3(self):
        sql = """desc format=json select * from temp"""
        result = parse(sql)
        expected = {"explain": {"from": "temp", "select": {"all_columns": {}}}, "format": "json"}
        self.assertEqual(result, expected)

    def test_merge_into(self):
        sql = """
            MERGE INTO TMP_TABLE1 TMP1
            USING TMP_TABLE1 TMP2
            ON TMP1.col1 =TMP2.col1
            AND TMP1.col2=TMP2.col2
            AND TMP1.col3=TMP2.col3
            AND (TMP2.col4 - 1) = TMP1.col4
            WHEN MATCHED THEN
            UPDATE SET ZTAGG_END = TMP2.ZTAGG"""
        result = parse(sql)
        expected = {
            "merge": {"when": "matched", "then": {"update": {"ZTAGG_END": "TMP2.ZTAGG"}}},
            "target": {"name": "TMP1", "value": "TMP_TABLE1"},
            "source": {"name": "TMP2", "value": "TMP_TABLE1"},
            "on": {"and": [
                {"eq": ["TMP1.col1", "TMP2.col1"]},
                {"eq": ["TMP1.col2", "TMP2.col2"]},
                {"eq": ["TMP1.col3", "TMP2.col3"]},
                {"eq": [{"sub": ["TMP2.col4", 1]}, "TMP1.col4"]},
            ]},
        }
        self.assertEqual(result, expected)

    def test_merge_top(self):
        # from https://www.sqlshack.com/understanding-the-sql-merge-statement/
        sql = """
            MERGE  TOP 10 percent
            TargetProducts AS Target
            USING SourceProducts AS Source
            ON Source.ProductID = Target.ProductID
            WHEN NOT MATCHED BY Target THEN
                INSERT (ProductID,ProductName, Price) 
                VALUES (Source.ProductID,Source.ProductName, Source.Price);
        """
        result = parse(sql)
        expected = {
            "merge": {
                "then": {
                    "insert": {},
                    "columns": ["ProductID", "ProductName", "Price"],
                    "values": ["Source.ProductID", "Source.ProductName", "Source.Price"],
                },
                "when": "not_matched_by_target",
            },
            "top": {"percent": 10},
            "on": {"eq": ["Source.ProductID", "Target.ProductID"]},
            "source": {"name": "Source", "value": "SourceProducts"},
            "target": {"name": "Target", "value": "TargetProducts"},
        }
        self.assertEqual(result, expected)

    def test_merge1(self):
        # from https://www.sqlshack.com/understanding-the-sql-merge-statement/
        sql = """
            MERGE TargetProducts AS Target
            USING SourceProducts AS Source
            ON Source.ProductID = Target.ProductID
            WHEN NOT MATCHED BY Target THEN
                INSERT (ProductID,ProductName, Price) 
                VALUES (Source.ProductID,Source.ProductName, Source.Price);
        """
        result = parse(sql)
        expected = {
            "merge": {
                "then": {
                    "insert": {},
                    "columns": ["ProductID", "ProductName", "Price"],
                    "values": ["Source.ProductID", "Source.ProductName", "Source.Price"],
                },
                "when": "not_matched_by_target",
            },
            "on": {"eq": ["Source.ProductID", "Target.ProductID"]},
            "source": {"name": "Source", "value": "SourceProducts"},
            "target": {"name": "Target", "value": "TargetProducts"},
        }
        self.assertEqual(result, expected)

    def test_merge2(self):
        # from https://www.sqlshack.com/understanding-the-sql-merge-statement/
        sql = """
            MERGE TargetProducts AS Target
            USING SourceProducts AS Source
            ON Source.ProductID = Target.ProductID
            
            -- For Inserts
            WHEN NOT MATCHED BY Target THEN
                INSERT (ProductID,ProductName, Price) 
                VALUES (Source.ProductID,Source.ProductName, Source.Price)
            
            -- For Updates
            WHEN MATCHED THEN UPDATE SET
                Target.ProductName = Source.ProductName,
                Target.Price  = Source.Price;
        """
        result = parse(sql)
        expected = {
            "merge": [
                {
                    "then": {
                        "columns": ["ProductID", "ProductName", "Price"],
                        "insert": {},
                        "values": ["Source.ProductID", "Source.ProductName", "Source.Price"],
                    },
                    "when": "not_matched_by_target",
                },
                {
                    "then": {"update": {"Target.Price": "Source.Price", "Target.ProductName": "Source.ProductName"}},
                    "when": "matched",
                },
            ],
            "on": {"eq": ["Source.ProductID", "Target.ProductID"]},
            "source": {"name": "Source", "value": "SourceProducts"},
            "target": {"name": "Target", "value": "TargetProducts"},
        }
        self.assertEqual(result, expected)

    def test_merge3(self):
        # from https://www.sqlshack.com/understanding-the-sql-merge-statement/
        sql = """ 
            MERGE TargetProducts AS Target
            USING SourceProducts AS Source
            ON Source.ProductID = Target.ProductID
                
            -- For Inserts
            WHEN NOT MATCHED BY Target THEN
                INSERT (ProductID,ProductName, Price) 
                VALUES (Source.ProductID,Source.ProductName, Source.Price)
                
            -- For Updates
            WHEN MATCHED THEN UPDATE SET
                Target.ProductName = Source.ProductName,
                Target.Price  = Source.Price
                
            -- For Deletes
            WHEN NOT MATCHED BY Source THEN
                DELETE;        
        """
        result = parse(sql)
        expected = {
            "merge": [
                {
                    "then": {
                        "columns": ["ProductID", "ProductName", "Price"],
                        "insert": {},
                        "values": ["Source.ProductID", "Source.ProductName", "Source.Price"],
                    },
                    "when": "not_matched_by_target",
                },
                {
                    "then": {"update": {"Target.Price": "Source.Price", "Target.ProductName": "Source.ProductName"}},
                    "when": "matched",
                },
                {"then": {"delete": {}}, "when": "not_matched_by_source"},
            ],
            "on": {"eq": ["Source.ProductID", "Target.ProductID"]},
            "source": {"name": "Source", "value": "SourceProducts"},
            "target": {"name": "Target", "value": "TargetProducts"},
        }
        self.assertEqual(result, expected)

    def test_issue_180_subsquery(self):
        sql = """SELECT concat( 
            ( SELECT value FROM schema.table a where b = c ), 
            RIGHT( '00' + CAST(MONTH(d) AS VARCHAR(2)), 2 ) 
        ) AS res"""
        result = parse(sql)
        expected = {"select": {
            "name": "res",
            "value": {"concat": [
                {
                    "from": {"name": "a", "value": "schema.table"},
                    "select": {"value": "value"},
                    "where": {"eq": ["b", "c"]},
                },
                {"right": [{"add": [{"literal": "00"}, {"cast": [{"month": "d"}, {"varchar": 2}]}]}, 2]},
            ]},
        }}
        self.assertEqual(result, expected)

    def test_issue_187_using_btree(self):
        sql = """create table tt (n varchar(10), nn varchar(6), key `inx_nn` (`nn`) using btree );"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [{"name": "n", "type": {"varchar": 10}}, {"name": "nn", "type": {"varchar": 6}}],
            "constraint": {"index": {"columns": "nn", "name": "inx_nn", "using": "btree"}},
            "name": "tt",
        }}
        self.assertEqual(result, expected)

    def test_using_btree_in_primary_key_1(self):
        sql = """create table tt (n varchar(10), nn varchar(6), primary key (`nn`) using btree );"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [{"name": "n", "type": {"varchar": 10}}, {"name": "nn", "type": {"varchar": 6}}],
            "constraint": {"primary_key": {"columns": "nn", "using": "btree"}},
            "name": "tt",
        }}
        self.assertEqual(result, expected)

    def test_using_btree_in_primary_key_2(self):
        sql = """create table tt (n varchar(10), nn varchar(6), primary key using btree (`nn`) );"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [{"name": "n", "type": {"varchar": 10}}, {"name": "nn", "type": {"varchar": 6}}],
            "constraint": {"primary_key": {"columns": "nn", "using": "btree"}},
            "name": "tt",
        }}
        self.assertEqual(result, expected)

    def test_issue_186_limit(self):
        sql = """SELECT * from t1 limit 1,10"""
        result = parse(sql)
        expected = {"select": {"all_columns": {}}, "from": "t1", "offset": 1, "limit": 10}
        self.assertEqual(result, expected)

    def test_issue_185_group_concat(self):
        sql = """SELECT substring_index(group_concat(manager.id order by manager.create DESC separator ','), ',', 1) AS s_id FROM a"""
        result = parse(sql)
        expected = {
            "from": "a",
            "select": {
                "name": "s_id",
                "value": {"substring_index": [
                    {
                        "group_concat": "manager.id",
                        "orderby": {"sort": "desc", "value": "manager.create"},
                        "separator": {"literal": ","},
                    },
                    {"literal": ","},
                    1,
                ]},
            },
        }
        self.assertEqual(result, expected)

    def test_issue_185_on_update(self):
        sql = """create table a (lastcreated datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)"""
        result = parse(sql)
        expected = {"create table": {
            "name": "a",
            "columns": {
                "default": "CURRENT_TIMESTAMP",
                "name": "lastcreated",
                "on_update": "CURRENT_TIMESTAMP",
                "type": {"datetime": {}},
            },
        }}
        self.assertEqual(result, expected)

    def test_issue_185_algorithm(self):
        # CREATE [OR REPLACE][ALGORITHM = {MERGE | TEMPTABLE | UNDEFINED}] VIEW
        sql = """CREATE OR REPLACE ALGORITHM = UNDEFINED VIEW view_name AS SELECT *"""
        result = parse(sql)
        expected = {"create view": {
            "algorithm": "undefined",
            "name": "view_name",
            "query": {"select": {"all_columns": {}}},
            "replace": True,
        }}

        self.assertEqual(result, expected)

    def test_issue_185_index_length(self):
        sql = """CREATE TABLE IF NOT EXISTS industry_i18n (id bigint(20) NOT NULL AUTO_INCREMENT, KEY locale_id (master_id,locale(255)));"""
        result = parse(sql)
        expected = {"create table": {
            "columns": {"auto_increment": True, "name": "id", "nullable": False, "type": {"bigint": 20}},
            "constraint": {"index": {
                "name": "locale_id",
                "columns": ["master_id", {"value": "locale", "length": 255}],
            }},
            "name": "industry_i18n",
            "replace": False,
        }}
        self.assertEqual(result, expected)

    def test_regexp(self):
        sql = """SELECT * FROM dbo.table where col  REGEXP '[^0-9A-Za-z]'"""
        result = parse(sql)
        expected = {
            "select": {"all_columns": {}},
            "from": "dbo.table",
            "where": {"regexp": ["col", {"literal": "[^0-9A-Za-z]"}]},
        }
        self.assertEqual(result, expected)

    def test_not_regexp(self):
        sql = """SELECT * FROM dbo.table where col NOT REGEXP '[^0-9A-Za-z]'"""
        result = parse(sql)
        expected = {
            "select": {"all_columns": {}},
            "from": "dbo.table",
            "where": {"not_regexp": ["col", {"literal": "[^0-9A-Za-z]"}]},
        }
        self.assertEqual(result, expected)

    def test_issue_192_delete1(self):
        sql = "DELETE FROM a LIMIT 1"
        result = parse(sql)
        expected = {"delete": "a", "limit": 1}
        self.assertEqual(result, expected)

    def test_issue_192_delete2(self):
        sql = "DELETE FROM a ORDER BY a.f DESC"
        result = parse(sql)
        expected = {"delete": "a", "orderby": {"sort": "desc", "value": "a.f"}}
        self.assertEqual(result, expected)

    def test_issue_192_delete3(self):
        sql = "DELETE LOW_PRIORITY FROM a"
        result = parse(sql)
        expected = {"delete": "a", "low_priority": True}
        self.assertEqual(result, expected)

    def test_issue_192_delete4(self):
        sql = "DELETE QUICK FROM a"
        result = parse(sql)
        expected = {"delete": "a", "quick": True}
        self.assertEqual(result, expected)

    def test_issue_192_delete5(self):
        sql = "DELETE IGNORE FROM a"
        result = parse(sql)
        expected = {"delete": "a", "ignore": True}
        self.assertEqual(result, expected)

    def test_issue_192_delete6(self):
        sql = "DELETE LOW_PRIORITY FROM a"
        result = parse(sql)
        expected = {"delete": "a", "low_priority": True}
        self.assertEqual(result, expected)

    def test_issue_192_delete7(self):
        sql = "DELETE t1 FROM table1 t1 WHERE t1.a IN (SELECT t2.a FROM table2 t2)"
        result = parse(sql)
        expected = {
            "delete": "t1",
            "from": {"name": "t1", "value": "table1"},
            "where": {"in": ["t1.a", {"from": {"name": "t2", "value": "table2"}, "select": {"value": "t2.a"}}]},
        }
        self.assertEqual(result, expected)

    def test_issue_192_delete8(self):
        sql = "DELETE a1, a2 FROM t1 AS a1 INNER JOIN t2 AS a2 WHERE a1.id=a2.id"
        result = parse(sql)
        expected = {
            "delete": ["a1", "a2"],
            "from": [{"name": "a1", "value": "t1"}, {"inner join": {"name": "a2", "value": "t2"}}],
            "where": {"eq": ["a1.id", "a2.id"]},
        }

        self.assertEqual(result, expected)

    def test_issue_192_delete9(self):
        sql = "DELETE FROM a1, a2 USING t1 AS a1 INNER JOIN t2 AS a2 WHERE a1.id=a2.id"
        result = parse(sql)
        expected = {
            "delete": ["a1", "a2"],
            "from": [{"name": "a1", "value": "t1"}, {"inner join": {"name": "a2", "value": "t2"}}],
            "where": {"eq": ["a1.id", "a2.id"]},
        }
        self.assertEqual(result, expected)

    def test_create_table_1(self):
        sql = """
            create table student (
                `name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_bin COMMENT 'name',
                `class` varchar(32) CHARACTER SET utf8 COLLATE utf8_bin COMMENT 'class',
            );
        """
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {
                    "character_set": "utf8mb4",
                    "collate": "utf8mb4_bin",
                    "comment": {"literal": "name"},
                    "name": "name",
                    "type": {"varchar": 32},
                },
                {
                    "character_set": "utf8",
                    "collate": "utf8_bin",
                    "comment": {"literal": "class"},
                    "name": "class",
                    "type": {"varchar": 32},
                },
            ],
            "name": "student",
        }}
        self.assertEqual(result, expected)

    def test_create_table_2(self):
        sql = """CREATE TABLE t2 (c1 INT) ROW_FORMAT=DEFAULT;"""
        result = parse(sql)
        expected = {"create table": {
            "columns": {"name": "c1", "type": {"int": {}}},
            "name": "t2",
            "row_format": "DEFAULT",
        }}
        self.assertEqual(result, expected)

    def test_create_table_3(self):
        sql = """CREATE TABLE t1 (a1 INT, KEY `idn_a1` (`a1`) USING BTREE COMMENT 't1 a1');"""
        result = parse(sql)
        expected = {"create table": {
            "columns": {"name": "a1", "type": {"int": {}}},
            "constraint": {"index": {
                "columns": "a1",
                "comment": {"literal": "t1 a1"},
                "name": "idn_a1",
                "using": "BTREE",
            }},
            "name": "t1",
        }}
        self.assertEqual(result, expected)

    def test_create_table_4(self):
        sql = """CREATE TABLE t1 (a1 INT, PRIMARY KEY (`a1`) USING BTREE COMMENT 't');"""
        result = parse(sql)
        expected = {"create table": {
            "columns": {"name": "a1", "type": {"int": {}}},
            "constraint": {"primary_key": {"columns": "a1", "comment": {"literal": "t"}, "using": "BTREE"}},
            "name": "t1",
        }}
        self.assertEqual(result, expected)

    def test_create_table_5(self):
        """CHECKSUM [=] {0 | 1}
        refer: https://dev.mysql.com/doc/refman/8.0/en/create-table.html
        """
        sql = """CREATE TABLE t1 (a1 varchar(8)) CHECKSUM=1;"""
        result = parse(sql)
        expected = {"create table": {"checksum": 1, "columns": {"name": "a1", "type": {"varchar": 8}}, "name": "t1"}}
        self.assertEqual(result, expected)

    def test_create_table_data_types_bit(self):
        """BIT[(M)]
        refer: https://dev.mysql.com/doc/refman/8.0/en/numeric-type-syntax.html
        """
        sql = """CREATE TABLE t1 (a1 bit, a2 bit(1));"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [{"name": "a1", "type": {"bit": {}}}, {"name": "a2", "type": {"bit": 1}},],
            "name": "t1",
        }}
        self.assertEqual(result, expected)

    def test_create_table_data_types_bigint(self):
        """ BIGINT[(M)] [UNSIGNED] [ZEROFILL] """
        sql = """CREATE TABLE tb (a1 bigint, a2 bigint(3), a3 BIGINT unsigned zerofill);"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "a1", "type": {"bigint": {}}},
                {"name": "a2", "type": {"bigint": 3}},
                {"name": "a3", "type": {"bigint": {}, "unsigned": True, "zerofill": True}},
            ],
            "name": "tb",
        }}
        self.assertEqual(result, expected)

    def test_create_table_data_types_decimal(self):
        """ DECIMAL[(M[,D])] [UNSIGNED] [ZEROFILL] """
        sql = """CREATE TABLE tb (a1 decimal, a2 decimal(3), a3 decimal(15,2), a4 DECIMAL unsigned zerofill)"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "a1", "type": {"decimal": {}}},
                {"name": "a2", "type": {"decimal": 3}},
                {"name": "a3", "type": {"decimal": [15, 2]}},
                {"name": "a4", "type": {"decimal": {}, "unsigned": True, "zerofill": True}},
            ],
            "name": "tb",
        }}
        self.assertEqual(result, expected)

    def test_create_table_data_types_double(self):
        """ DOUBLE[(M,D)] [UNSIGNED] [ZEROFILL] """
        sql = """CREATE TABLE tb (a1 double, a2 double(10,4), a3 DOUBLE unsigned zerofill);"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "a1", "type": {"double": {}}},
                {"name": "a2", "type": {"double": [10, 4]}},
                {"name": "a3", "type": {"double": {}, "unsigned": True, "zerofill": True}},
            ],
            "name": "tb",
        }}
        self.assertEqual(result, expected)

    def test_create_table_data_types_float(self):
        """ FLOAT[(M,D)] [UNSIGNED] [ZEROFILL] """
        sql = """CREATE TABLE tb (a1 float, a2 float(53,0), a3 FLOAT unsigned zerofill);"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "a1", "type": {"float": {}}},
                {"name": "a2", "type": {"float": [53, 0]}},
                {"name": "a3", "type": {"float": {}, "unsigned": True, "zerofill": True}},
            ],
            "name": "tb",
        }}
        self.assertEqual(result, expected)

    def test_create_table_data_types_int(self):
        """ INT[(M)] [UNSIGNED] [ZEROFILL] """
        sql = """CREATE TABLE tb (a1 int, a2 int(3), a3 INT unsigned zerofill);"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "a1", "type": {"int": {}}},
                {"name": "a2", "type": {"int": 3}},
                {"name": "a3", "type": {"int": {}, "unsigned": True, "zerofill": True}},
            ],
            "name": "tb",
        }}
        self.assertEqual(result, expected)

    def test_create_table_data_types_integer(self):
        """ INTEGER[(M)] [UNSIGNED] [ZEROFILL] """
        sql = """CREATE TABLE tb (a1 integer, a2 integer(3), a3 INTEGER unsigned zerofill);"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "a1", "type": {"integer": {}}},
                {"name": "a2", "type": {"integer": 3}},
                {"name": "a3", "type": {"integer": {}, "unsigned": True, "zerofill": True}},
            ],
            "name": "tb",
        }}
        self.assertEqual(result, expected)

    def test_create_table_data_types_mediumint(self):
        """ MEDIUMINT[(M)] [UNSIGNED] [ZEROFILL] """
        sql = """CREATE TABLE tb (a1 mediumint, a2 mediumint(3), a3 MEDIUMINT unsigned zerofill);"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "a1", "type": {"mediumint": {}}},
                {"name": "a2", "type": {"mediumint": 3}},
                {"name": "a3", "type": {"mediumint": {}, "unsigned": True, "zerofill": True}},
            ],
            "name": "tb",
        }}
        self.assertEqual(result, expected)

    def test_create_table_dta_types_smallint(self):
        """SMALLINT[(M)]
        refer: https://dev.mysql.com/doc/refman/8.0/en/numeric-type-syntax.html
        """
        sql = """CREATE TABLE tb (a1 smallint, a2 smallint(3), a3 SMALLINT unsigned zerofill);"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "a1", "type": {"smallint": {}}},
                {"name": "a2", "type": {"smallint": 3}},
                {"name": "a3", "type": {"smallint": {}, "unsigned": True, "zerofill": True}},
            ],
            "name": "tb",
        }}
        self.assertEqual(result, expected)

    def test_create_table_dta_types_tinyint(self):
        """TINYINT[(M)] [UNSIGNED] [ZEROFILL][(M)]
        refer: https://dev.mysql.com/doc/refman/8.0/en/numeric-type-syntax.html
        """
        sql = """CREATE TABLE tb (a1 tinyint, a2 tinyint(3), a3 TINYINT unsigned zerofill);"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "a1", "type": {"tinyint": {}}},
                {"name": "a2", "type": {"tinyint": 3}},
                {"name": "a3", "type": {"tinyint": {}, "unsigned": True, "zerofill": True}},
            ],
            "name": "tb",
        }}
        self.assertEqual(result, expected)

    def test_create_table_dta_types_timestamp(self):
        """TIMESTAMP[(M)]
        refer: https://dev.mysql.com/doc/refman/8.0/en/datetime.html
        """
        sql = """
            CREATE TABLE tb (
                `update_time` TIMESTAMP ON UPDATE CURRENT_TIMESTAMP(3),
                `create_time` TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
            );
        """
        result = parse(sql)
        expected = {"create table": {
            "columns": [
                {"name": "update_time", "on_update": {"current_timestamp": 3}, "type": {"timestamp": {}}},
                {
                    "default": {"current_timestamp": 3},
                    "name": "create_time",
                    "nullable": False,
                    "type": {"timestamp": 3},
                },
            ],
            "name": "tb",
        }}

    def test_update_order_by_limit(self):
        """
        refer: https://dev.mysql.com/doc/refman/5.7/en/update.html
        """
        sql = "UPDATE tb1 a SET a1='', a2 = now() WHERE a3='' ORDER BY a4 LIMIT 1, 2"
        result = parse(sql)
        expected = {
            "update": {"name": "a", "value": "tb1"},
            "set": {"a1": {"literal": ""}, "a2": {"now": {}}},
            "where": {"eq": ["a3", {"literal": ""}]},
            "orderby": {"value": "a4"},
            "limit": 2,
            "offset": 1,
        }
        self.assertEqual(result, expected)

    def test_update_join(self):
        """
        refer: https://dev.mysql.com/doc/refman/5.7/en/update.html
        """
        sql = """
            UPDATE tb1 a LEFT JOIN tb2 b ON a.a1 = b.b1 LEFT JOIN tb3 c ON a.a2 = c.c2 
            SET a.a3 = b.b3, a.a4 = c.c4 
            WHERE a.a5 = ''
        """
        result = parse(sql)
        expected = {
            "set": {"a.a3": "b.b3", "a.a4": "c.c4"},
            "update": [
                {"name": "a", "value": "tb1"},
                {"left join": {"name": "b", "value": "tb2"}, "on": {"eq": ["a.a1", "b.b1"]}},
                {"left join": {"name": "c", "value": "tb3"}, "on": {"eq": ["a.a2", "c.c2"]}},
            ],
            "where": {"eq": ["a.a5", {"literal": ""}]},
        }
        self.assertEqual(result, expected)

    def test_straight_join_1(self):
        sql = "SELECT * FROM table1 t1 STRAIGHT_JOIN table3 t3"
        result = parse(sql)
        expected = {
            "from": [{"name": "t1", "value": "table1"}, {"straight_join": {"name": "t3", "value": "table3"}},],
            "select": {"all_columns": {}},
        }
        self.assertEqual(result, expected)

    def test_straight_join_2(self):
        sql = "SELECT * FROM table1 t1 STRAIGHT_JOIN table3 t3 ON t1.id = t3.id"
        result = parse(sql)
        expected = {
            "from": [
                {"name": "t1", "value": "table1"},
                {"on": {"eq": ["t1.id", "t3.id"]}, "straight_join": {"name": "t3", "value": "table3"}},
            ],
            "select": {"all_columns": {}},
        }
        self.assertEqual(result, expected)

    def test_straight_join_3(self):
        result = parse("SELECT t1.field1 FROM t1 STRAIGHT_JOIN t2 ON t1.id = t2.id STRAIGHT_JOIN t3 USING id")
        expected = {
            "select": {"value": "t1.field1"},
            "from": [
                "t1",
                {"straight_join": "t2", "on": {"eq": ["t1.id", "t2.id"]}},
                {"straight_join": "t3", "using": "id"},
            ],
        }
        self.assertEqual(result, expected)

    def test_issue_199_convert1(self):
        sql = "SELECT CAST('2000-01-01' AS DATE),  CAST('123' AS UNSIGNED INTEGER), CAST('123' AS SIGNED INTEGER)"
        result = parse(sql)
        expected = {"select": [
            {"value": {"cast": [{"literal": "2000-01-01"}, {"date": {}}]}},
            {"value": {"cast": [{"literal": "123"}, {"bigint": {}, "unsigned": True}]}},
            {"value": {"cast": [{"literal": "123"}, {"bigint": {}}]}},
        ]}
        self.assertEqual(result, expected)

    def test_issue_199_convert2(self):
        sql = "SELECT a1 FROM tb WHERE a2=CAST(CAST(1 - 2 AS UNSIGNED) AS SIGNED)"
        result = parse(sql)
        expected = {
            "from": "tb",
            "select": {"value": "a1"},
            "where": {"eq": [
                "a2",
                {"cast": [{"cast": [{"sub": [1, 2]}, {"bigint": {}, "unsigned": True}]}, {"bigint": {}}]},
            ]},
        }

        self.assertEqual(result, expected)

    def test_issue_199_convert3(self):
        sql = "SELECT CAST('test' AS CHAR CHARACTER SET utf8) COLLATE utf8_bin"
        result = parse(sql)
        expected = {"select": {"value": {"collate": [
            {"cast": [{"literal": "test"}, {"char": {}, "character_set": "utf8"}]},
            "utf8_bin",
        ]}}}
        self.assertEqual(result, expected)

    def test_issue_199_convert4(self):
        sql = "SELECT CONVERT('test' USING utf8)"
        result = parse(sql)
        expected = {"select": {"value": {"convert": [{"literal": "test"}, {"using": "utf8"}]}}}
        self.assertEqual(result, expected)

    def test_issue_199_convert5(self):
        sql = "SELECT CONVERT('test' USING utf8) COLLATE utf8_bin"
        result = parse(sql)
        expected = {"select": {"value": {"collate": [
            {"convert": [{"literal": "test"}, {"using": "utf8"}]},
            "utf8_bin",
        ]}}}

        self.assertEqual(result, expected)

    def test_issue_199_convert6(self):
        sql = "SELECT CONVERT('test', CHAR CHARACTER SET utf8) COLLATE utf8_bin"
        result = parse(sql)
        expected = {"select": {"value": {"collate": [
            {"convert": [{"literal": "test"}, {"char": {}, "character_set": "utf8"}]},
            "utf8_bin",
        ]}}}
        self.assertEqual(result, expected)

    def test_issue_200_assign(self):
        sql = "SELECT @var1 := 1, @var2 := @var1 + 1;"
        result = parse(sql)
        expected = {"select": [
            {"value": {"assign": ["@var1", 1]}},
            {"value": {"assign": ["@var2", {"add": ["@var1", 1]}]}},
        ]}
        self.assertEqual(result, expected)

    def test_issue_218_udf(self):
        from tests.mysql.issue_218 import expectations

        content = File("tests/mysql/issue_218.sql").read()
        blocks = list(parse_delimiters(content, ignore=None))
        for i, (sql, expected) in enumerate(zip_longest(blocks, expectations)):
            try:
                result = parse(sql)
                assertAlmostEqual(result, expected)
                assertAlmostEqual(expected, result)
            except Exception as cause:
                raise cause

    def test_issue_218_comment(self):
        sql = """/*!50610 SET @@default_storage_engine = 'InnoDB'*/;"""
        result = parse(sql)
        self.assertIsNone(result)

    def test_issue_218_trigger(self):
        sql = """
        DELIMITER ;;
        CREATE TRIGGER `ins_film` AFTER INSERT ON `film` FOR EACH ROW BEGIN
            INSERT INTO film_text (film_id, title, description)
                VALUES (new.film_id, new.title, new.description);
          END;;
        """
        parse("DELIMITER ;;")
        result = parse(sql)
        expected = [
            {"delimiter": ";;"},
            {"create_trigger": {
                "body": {"block": {
                    "columns": ["film_id", "title", "description"],
                    "insert": "film_text",
                    "query": {"select": [
                        {"value": "new.film_id"},
                        {"value": "new.title"},
                        {"value": "new.description"},
                    ]},
                }},
                "event": "insert",
                "name": "ins_film",
                "table": "film",
                "when": "after",
            }},
        ]
        self.assertEqual(result, expected)

    def test_issue_218_procedure(self):
        sql = """
        CREATE PROCEDURE rewards_report (
            IN min_monthly_purchases TINYINT UNSIGNED
            , IN min_dollar_amount_purchased DECIMAL(10,2)
            , OUT count_rewardees INT
        )
        LANGUAGE SQL
        NOT DETERMINISTIC
        READS SQL DATA
        SQL SECURITY DEFINER
        COMMENT 'Provides a customizable report on best customers'
        proc: BEGIN
        END"""
        result = parse(sql)
        expected = {"create_procedure": {
            "body": {"label": "proc"},
            "comment": {"literal": "Provides a customizable report on best customers"},
            "language": "sql",
            "name": "rewards_report",
            "params": [
                {"mode": "in", "name": "min_monthly_purchases", "type": {"tinyint": {}, "unsigned": True}},
                {"mode": "in", "name": "min_dollar_amount_purchased", "type": {"decimal": [10, 2]}},
                {"mode": "out", "name": "count_rewardees", "type": {"int": {}}},
            ],
            "sql_security": "definer",
        }}
        self.assertEqual(result, expected)

    def test_issue_218_transaction(self):
        sql = """
        START TRANSACTION;
        COMMIT;
        ROLLBACK;
        """
        result = parse(sql)
        expected = [
            {"start_transaction": {}},
            {"commit": {}},
            {"rollback": {}},
        ]
        self.assertEqual(result, expected)

    """
    Tests to cover some permutations on the REPLACE statement with this grammer
    15.2.12 REPLACE Statement

    REPLACE [LOW_PRIORITY | DELAYED]
        [INTO] tbl_name
        [PARTITION (partition_name [, partition_name] ...)]
        [(col_name [, col_name] ...)]
        { {VALUES | VALUE} (value_list) [, (value_list)] ...
          |
          VALUES row_constructor_list
        }
    
    REPLACE [LOW_PRIORITY | DELAYED]
        [INTO] tbl_name
        [PARTITION (partition_name [, partition_name] ...)]
        SET assignment_list
    
    REPLACE [LOW_PRIORITY | DELAYED]
        [INTO] tbl_name
        [PARTITION (partition_name [, partition_name] ...)]
        [(col_name [, col_name] ...)]
        {SELECT ... | TABLE table_name}
    
    value:
        {expr | DEFAULT}
    
    value_list:
        value [, value] ...
    
    row_constructor_list:
        ROW(value_list)[, ROW(value_list)][, ...]
    
    assignment:
        col_name = value
    
    assignment_list:
        assignment [, assignment] ...
        
    """

    def test_pr_236_replace1(self):
        sql = """
        REPLACE INTO test_table (id, name) VALUES (1, 'New Name')        
        """
        result = parse(sql)
        expected = {
            "replace": "test_table",
            "columns": ["id", "name"],
            "query": {"select": [{"value": 1}, {"value": {"literal": "New Name"}}]},
        }
        self.assertEqual(result, expected)

    def test_pr_236_replace2(self):
        sql = """REPLACE INTO tab (name) VALUES(42)"""
        result = parse(sql)
        expected = {
            "columns": "name",
            "replace": "tab",
            "query": {"select": {"value": 42}},
        }
        self.assertEqual(result, expected)

    def test_pr_236_replace3(self):
        sql = """replace into t (a, b, c) select x, y, z from f"""
        result = parse(sql)
        expected = {
            "columns": ["a", "b", "c"],
            "replace": "t",
            "query": {"from": "f", "select": [{"value": "x"}, {"value": "y"}, {"value": "z"}]},
        }
        self.assertEqual(result, expected)

    def test_pr_236_replace4(self):
        sql = """REPLACE Person(Id, Name, DateOfBirth, Gender)
            VALUES (1, 'John Lennon', '1940-10-09', 'M'), (2, 'Paul McCartney', '1942-06-18', 'M'),
            (3, 'George Harrison', '1943-02-25', 'M'), (4, 'Ringo Starr', '1940-07-07', 'M')"""
        result = parse(sql)
        expected = {
            "replace": "Person",
            "values": [
                {"DateOfBirth": "1940-10-09", "Gender": "M", "Id": 1, "Name": "John Lennon"},
                {"DateOfBirth": "1942-06-18", "Gender": "M", "Id": 2, "Name": "Paul McCartney"},
                {"DateOfBirth": "1943-02-25", "Gender": "M", "Id": 3, "Name": "George Harrison"},
                {"DateOfBirth": "1940-07-07", "Gender": "M", "Id": 4, "Name": "Ringo Starr"},
            ],
        }
        self.assertEqual(result, expected)

    def test_pr_236_while1(self):
        sql = """
        CREATE PROCEDURE dowhile()
        BEGIN
          DECLARE v1 INT DEFAULT 5;

          WHILE v1 > 0 DO
            SET v1 = v1 - 1;
          END WHILE;
        END;"""

        result = parse(sql)
        expected = {"create_procedure": {
            "name": "dowhile",
            "body": {"block": [
                {"declare": {"name": "v1", "default": 5, "type": {"int": {}}}},
                {"while": {"gt": ["v1", 0]}, "do": {"set": {"v1": {"sub": ["v1", 1]}}},},
            ]},
        }}
        self.assertEqual(result, expected)

    def test_pr_236_while2(self):
        sql = """
        CREATE PROCEDURE dowhile()
        BEGIN
          DECLARE v1 INT DEFAULT 5;

          WHILE v1 > 0 DO
            SET v1 = v1 - 1;
            SET v2 = v2 + 1;
          END WHILE;
        END;"""

        result = parse(sql)
        expected = {"create_procedure": {
            "name": "dowhile",
            "body": {"block": [
                {"declare": {"name": "v1", "default": 5, "type": {"int": {}}}},
                {
                    "while": {"gt": ["v1", 0]},
                    "do": [{"set": {"v1": {"sub": ["v1", 1]}}}, {"set": {"v2": {"add": ["v2", 1]}}},],
                },
            ]},
        }}
        self.assertEqual(result, expected)

    def test_pr_236_cursor(self):
        sql = """
        CREATE PROCEDURE demo()
        BEGIN
          DECLARE done INT DEFAULT FALSE;
          DECLARE a CHAR(16);
          DECLARE cur1 CURSOR FOR SELECT id,data FROM test.t1;
          DECLARE cur2 CURSOR FOR SELECT i FROM test.t2;
          DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;
        
          OPEN cur1;
          OPEN cur2;
        
          read_loop: LOOP
            FETCH cur1 INTO a, b;
            FETCH cur2 INTO c;
            IF done THEN
              LEAVE read_loop;
            END IF;
            IF b < c THEN
              INSERT INTO test.t3 VALUES (a,b);
            ELSE
              INSERT INTO test.t3 VALUES (a,c);
            END IF;
          END LOOP;
        
          CLOSE cur1;
          CLOSE cur2;
        END;
        """
        result = parse(sql)
        expected = {"create_procedure": {
            "name": "demo",
            "body": {"block": [
                {"declare": {"name": "done", "type": {"int": {}}, "default": False}},
                {"declare": {"name": "a", "type": {"char": 16}}},
                {"declare_cursor": {
                    "name": "cur1",
                    "query": {"select": [{"value": "id"}, {"value": "data"}], "from": "test.t1"},
                }},
                {"declare_cursor": {"name": "cur2", "query": {"select": {"value": "i"}, "from": "test.t2"}}},
                {"declare_handler": {
                    "action": "continue",
                    "conditions": "not_found",
                    "body": {"set": {"done": True}},
                }},
                {"open": "cur1"},
                {"open": "cur2"},
                {
                    "label": "read_loop",
                    "loop": [
                        {"fetch": "cur1"},
                        {"fetch": "cur2"},
                        {"if": "done", "then": {"leave": "read_loop"}},
                        {
                            "if": {"lt": ["b", "c"]},
                            "then": {"query": {"select": [{"value": "a"}, {"value": "b"}]}, "insert": "test.t3"},
                            "else": {"query": {"select": [{"value": "a"}, {"value": "c"}]}, "insert": "test.t3"},
                        },
                    ],
                },
                {"close": "cur1"},
                {"close": "cur2"},
            ]},
        }}
        self.assertEqual(result, expected)

    @skip("Not implemented yet")
    def test_multiple_vars_in_declare(self):
        sql = """
        CREATE PROCEDURE curdemo()
        BEGIN
          DECLARE b, c INT;
        END;
        """
        result = parse(sql)
        expected = {"create_procedure": {
            "name": "curdemo",
            "body": {"block": [
                {"declare": {"name": "b", "type": {"int": {}}}},
                {"declare": {"name": "c", "type": {"int": {}}}},
            ]},
        }}
        self.assertEqual(result, expected)

    def test_declare_cursor(self):
        sql = """
        CREATE PROCEDURE demo()
        BEGIN
          DECLARE cur1 CURSOR FOR SELECT id,data FROM test.t1;
        END;
        """
        result = parse(sql)
        expected = {"create_procedure": {
            "name": "demo",
            "body": {
                "block": {"declare_cursor": {
                    "name": "cur1",
                    "query": {"select": [{"value": "id"}, {"value": "data"}], "from": "test.t1"},
                }},
            },
        }}
        self.assertEqual(result, expected)

    def test_call_0(self):
        sql = """
        CREATE PROCEDURE demo()
        BEGIN
            CALL my_procedure();
        END;
        """
        result = parse(sql)
        expected = {"create_procedure": {"name": "demo", "body": {"block": {"op": "my_procedure"}}}}
        self.assertEqual(result, expected)

    def test_call_0b(self):
        sql = """
        CREATE PROCEDURE demo()
        BEGIN
            CALL my_procedure;
        END;
        """
        result = parse(sql)
        expected = {"create_procedure": {"name": "demo", "body": {"block": {"op": "my_procedure"}}}}
        self.assertEqual(result, expected)

    def test_call_1(self):
        sql = """
        CREATE PROCEDURE demo()
        BEGIN
            CALL my_procedure(1);
        END;
        """
        result = parse(sql)
        expected = {"create_procedure": {"name": "demo", "body": {"block": {"op": "my_procedure", "args": 1}}}}
        self.assertEqual(result, expected)

    def test_call_3(self):
        sql = """
        CREATE PROCEDURE demo()
        BEGIN
            CALL my_procedure(1, 'test', @output_param);
        END;
        """
        result = parse(sql)
        expected = {"create_procedure": {
            "name": "demo",
            "body": {"block": {"op": "my_procedure", "args": [1, {"literal": "test"}, "@output_param"]}},
        }}
        self.assertEqual(result, expected)
