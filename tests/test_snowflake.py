# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from unittest import TestCase

from mo_testing.fuzzytestcase import add_error_reporting

from mo_sql_parsing import parse, normal_op


@add_error_reporting
class TestSnowflake(TestCase):
    def test_issue_101_create_temp_table(self):
        sql = """CREATE TEMP TABLE foo(a varchar(10))"""
        result = parse(sql)
        expected = {"create table": {
            "columns": {"name": "a", "type": {"varchar": 10}},
            "name": "foo",
            "temporary": True,
        }}
        self.assertEqual(result, expected)

    def test_issue_101_create_transient_table(self):
        sql = """CREATE TRANSIENT TABLE foo(a varchar(10))"""
        result = parse(sql)
        expected = {"create table": {
            "columns": {"name": "a", "type": {"varchar": 10}},
            "name": "foo",
            "transient": True,
        }}
        self.assertEqual(result, expected)

    def test_issue_102_table_functions1(self):
        sql = """
        SELECT seq4()
        FROM TABLE(generator(rowcount => 10))
        """
        result = parse(sql)
        expected = {
            "from": {"table": {"generator": {}, "rowcount": 10}},
            "select": {"value": {"seq4": {}}},
        }
        self.assertEqual(result, expected)

    def test_issue_102_table_functions2(self):
        sql = """
        SELECT uniform(1, 10, random())
        FROM TABLE(generator(rowcount => 5));
        """
        result = parse(sql)
        expected = {
            "from": {"table": {"generator": {}, "rowcount": 5}},
            "select": {"value": {"uniform": [1, 10, {"random": {}}]}},
        }
        self.assertEqual(result, expected)

    def test_issue_102_table_functions3(self):
        sql = """
        SELECT seq4()
        FROM TABLE(generator(rowcount => 10))
        """
        result = parse(sql, calls=normal_op)
        expected = {
            "from": {"op": "table", "args": [{"op": "generator", "kwargs": {"rowcount": 10}}]},
            "select": {"value": {"op": "seq4"}},
        }
        self.assertEqual(result, expected)

    def test_issue_102_table_functions4(self):
        sql = """
        SELECT uniform(1, 10, random())
        FROM TABLE(generator(rowcount => 5));
        """
        result = parse(sql, calls=normal_op)
        expected = {
            "from": {"op": "table", "args": [{"op": "generator", "kwargs": {"rowcount": 5}}]},
            "select": {"value": {"op": "uniform", "args": [1, 10, {"op": "random"}]}},
        }

        self.assertEqual(result, expected)

    def test_issue_102_table_functions5(self):
        sql = """
        SELECT t.index, t.value
        FROM TABLE(split_to_table('a.b.z.d', '.')) as t
        ORDER BY t.value;
        """
        result = parse(sql)
        expected = {
            "from": {"name": "t", "value": {"table": {"split_to_table": [{"literal": "a.b.z.d"}, {"literal": "."}]}},},
            "orderby": {"value": "t.value"},
            "select": [{"value": "t.index"}, {"value": "t.value"}],
        }
        self.assertEqual(result, expected)

    def test_issue_102_within_group(self):
        sql = """
        SELECT listagg(name, ', ' ) WITHIN GROUP (ORDER BY name) AS names
        FROM names_table
        """
        result = parse(sql)
        expected = {
            "from": "names_table",
            "select": {
                "name": "names",
                "value": {"listagg": ["name", {"literal": ", "}]},
                "within": {"orderby": {"value": "name"}},
            },
        }
        self.assertEqual(result, expected)

    def test_issue_105_multiline_strings(self):
        sql = """SELECT 'one
            two
            three'
            FROM my_table"""
        result = parse(sql)
        expected = {
            "from": "my_table",
            "select": {"value": {"literal": "one\n            two\n            three"}},
        }
        self.assertEqual(result, expected)

    def test_issue_104_character_varying1(self):
        sql = """CREATE TABLE foo(a CHARACTER(5))"""
        result = parse(sql)
        expected = {"create table": {"columns": {"name": "a", "type": {"character": 5}}, "name": "foo"}}
        self.assertEqual(result, expected)

    def test_issue_104_character_varying2(self):
        sql = """CREATE TABLE foo(a CHARACTER VARYING(5))"""
        result = parse(sql)
        expected = {"create table": {"columns": {"name": "a", "type": {"character_varying": 5}}, "name": "foo"}}
        self.assertEqual(result, expected)

    def test_issue_106_index_column_name1(self):
        sql = """SELECT index FROM my_table;"""
        result = parse(sql)
        expected = {"from": "my_table", "select": {"value": "index"}}
        self.assertEqual(result, expected)

    def test_issue_106_index_column_name2(self):
        sql = """CREATE TABLE my_table(index INTEGER);"""
        result = parse(sql)
        expected = {"create table": {"columns": {"name": "index", "type": {"integer": {}}}, "name": "my_table"}}
        self.assertEqual(result, expected)

    def test_issue_107_lateral_function(self):
        sql = """SELECT emp.employee_id, emp.last_name, value AS project_name
        FROM employees AS emp, LATERAL flatten(input => emp.project_names) AS proj_names
        ORDER BY employee_id;"""
        result = parse(sql)
        expected = {
            "from": [
                {"name": "emp", "value": "employees"},
                {"lateral": {"name": "proj_names", "value": {"flatten": {}, "input": "emp.project_names"}}},
            ],
            "orderby": {"value": "employee_id"},
            "select": [
                {"value": "emp.employee_id"},
                {"value": "emp.last_name"},
                {"name": "project_name", "value": "value"},
            ],
        }
        self.assertEqual(result, expected)

    def test_issue_108_colon1(self):
        sql = """SELECT src:dealership FROM car_sales"""
        result = parse(sql)
        expected = {
            "from": "car_sales",
            "select": {"value": {"get": ["src", {"literal": "dealership"}]}},
        }
        self.assertEqual(result, expected)

    def test_issue_108_colon2(self):
        sql = """SELECT src:salesperson.name FROM car_sales"""
        result = parse(sql)
        expected = {
            "from": "car_sales",
            "select": {"value": {"get": ["src", {"literal": "salesperson"}, {"literal": "name"}]}},
        }
        self.assertEqual(result, expected)

    def test_issue_108_colon3(self):
        sql = """SELECT src:['salesperson']['name'] FROM car_sales"""
        result = parse(sql)
        expected = {
            "from": "car_sales",
            "select": {"value": {"get": ["src", {"literal": "salesperson"}, {"literal": "name"}]}},
        }
        self.assertEqual(result, expected)

    def test_issue_110_double_quote(self):
        sql = """SELECT REPLACE(foo, '"', '') AS bar FROM my_table"""
        result = parse(sql)
        expected = {
            "from": "my_table",
            "select": {"name": "bar", "value": {"replace": ["foo", {"literal": '"'}, {"literal": ""}]}},
        }
        self.assertEqual(result, expected)

    def test_issue_109_qualify1(self):
        sql = """SELECT id, row_number() OVER (PARTITION BY id ORDER BY id) AS row_num
        FROM my_table
        QUALIFY row_num = 1"""
        result = parse(sql)
        expected = {
            "from": "my_table",
            "qualify": {"eq": ["row_num", 1]},
            "select": [
                {"value": "id"},
                {
                    "name": "row_num",
                    "over": {"orderby": {"value": "id"}, "partitionby": "id"},
                    "value": {"row_number": {}},
                },
            ],
        }

        self.assertEqual(result, expected)

    def test_issue_109_qualify2(self):
        sql = """SELECT id, names
        FROM my_table
        QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY id) = 1"""
        result = parse(sql)
        expected = {
            "from": "my_table",
            "qualify": {"eq": [
                {"over": {"orderby": {"value": "id"}, "partitionby": "id"}, "value": {"row_number": {}}},
                1,
            ]},
            "select": [{"value": "id"}, {"value": "names"}],
        }
        self.assertEqual(result, expected)

    def test_issue_112_qualify(self):
        sql = """SELECT 
            a
        FROM 
            a
        QUALIFY
            ROW_NUMBER() OVER
            (PARTITION BY ssmu.cak, ssmu.rsd  ORDER BY created_at DESC) = 1"""
        result = parse(sql)
        expected = {
            "from": "a",
            "qualify": {"eq": [
                {
                    "over": {
                        "orderby": {"sort": "desc", "value": "created_at"},
                        "partitionby": ["ssmu.cak", "ssmu.rsd"],
                    },
                    "value": {"row_number": {}},
                },
                1,
            ]},
            "select": {"value": "a"},
        }
        self.assertEqual(result, expected)

    def test_issue_101_ilike(self):
        sql = """SELECT * 
        FROM my_table 
        WHERE subject ILIKE '%j%do%'"""
        result = parse(sql)
        expected = {
            "from": "my_table",
            "select": {"all_columns": {}},
            "where": {"ilike": ["subject", {"literal": "%j%do%"}]},
        }
        self.assertEqual(result, expected)

    def test_issue_113_dash_in_identifier(self):
        sql = """SELECT SUM(a-b) AS diff
        FROM my_table"""
        result = parse(sql)
        expected = {
            "from": "my_table",
            "select": {"name": "diff", "value": {"sum": {"sub": ["a", "b"]}}},
        }
        self.assertEqual(result, expected)

    def test_issue_114_pivot(self):
        sql = """SELECT *
          FROM (SELECT * FROM monthly_sales_table) monthly_sales
            PIVOT(SUM(amount) FOR month IN ('JAN', 'FEB', 'MAR', 'APR')) AS p
        """
        result = parse(sql)
        expected = {
            "from": [
                {"name": "monthly_sales", "value": {"select": {"all_columns": {}}, "from": "monthly_sales_table"}},
                {
                    "pivot": {
                        "name": "p",
                        "aggregate": {"sum": "amount"},
                        "for": "month",
                        "in": {"literal": ["JAN", "FEB", "MAR", "APR"]},
                    },
                },
            ],
            "select": {"all_columns": {}},
        }

        self.assertEqual(result, expected)

    def test_unpivot(self):
        sql = """SELECT * FROM monthly_sales
        UNPIVOT(sales FOR month IN (jan, feb, mar, april))
        ORDER BY empid;
        """
        result = parse(sql)
        expected = {
            "from": [
                "monthly_sales",
                {"unpivot": {"value": "sales", "for": "month", "in": ["jan", "feb", "mar", "april"]}},
            ],
            "orderby": {"value": "empid"},
            "select": {"all_columns": {}},
        }

        self.assertEqual(result, expected)

    def test_issue_116_select_w_quotes1(self):
        sql = """SELECT src:"sales-person".name
        FROM car_sales"""
        result = parse(sql)
        expected = {
            "from": "car_sales",
            "select": {"value": {"get": ["src", {"literal": "sales-person"}, {"literal": "name"}]}},
        }
        self.assertEqual(result, expected)

    def test_issue_116_select_w_quotes2(self):
        sql = """SELECT src:".".name
        FROM car_sales"""
        result = parse(sql)
        expected = {
            "from": "car_sales",
            "select": {"value": {"get": ["src", {"literal": "."}, {"literal": "name"}]}},
        }
        self.assertEqual(result, expected)

    def test_issue_118_set1(self):
        sql = """ALTER SESSION SET TIMESTAMP_TYPE_MAPPING = TIMESTAMP_NTZ"""
        result = parse(sql)
        expected = {"set": {"timestamp_type_mapping": "timestamp_ntz"}}
        self.assertEqual(result, expected)

    def test_issue_118_set2(self):
        sql = """ALTER SESSION SET LOCK_TIMEOUT = 3600*2"""
        result = parse(sql)
        expected = {"set": {"lock_timeout": {"mul": [3600, 2]}}}
        self.assertEqual(result, expected)

    def test_issue_118_unset(self):
        sql = """ALTER SESSION UNSET LOCK_TIMEOUT"""
        result = parse(sql)
        expected = {"unset": "lock_timeout"}
        self.assertEqual(result, expected)

    def test_issue_121_many_concat(self):
        sql = "SELECT a" + (" || a" * 300)
        result = parse(sql)
        expected = {"select": {"value": {"concat": ["a"] * 301}}}
        self.assertEqual(result, expected)

    def test_issue_119_copy1(self):
        sql = """COPY INTO mytable FROM @my_int_stage"""
        result = parse(sql)
        expected = {"copy": {"from": "@my_int_stage", "into": "mytable"}}
        self.assertEqual(result, expected)

    def test_issue_119_copy2(self):
        sql = """COPY INTO mytable FILE_FORMAT = (TYPE = CSV)"""
        result = parse(sql)
        expected = {"copy": {"file_format": {"type": "CSV"}, "into": "mytable"}}
        self.assertEqual(result, expected)

    def test_issue_119_copy3(self):
        sql = """COPY INTO mytable from @~/staged FILE_FORMAT = (FORMAT_NAME = 'mycsv')"""
        result = parse(sql)
        expected = {"copy": {
            "file_format": {"format_name": {"literal": "mycsv"}},
            "from": "@~/staged",
            "into": "mytable",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copy4(self):
        sql = """COPY INTO mycsvtable FROM @my_ext_stage/tutorials/dataloading/contacts1.csv;"""
        result = parse(sql)
        expected = {"copy": {"from": "@my_ext_stage/tutorials/dataloading/contacts1.csv", "into": "mycsvtable"}}
        self.assertEqual(result, expected)

    def test_issue_119_copy5(self):
        sql = """COPY INTO mytable
            FROM s3://mybucket/data/files
            STORAGE_INTEGRATION = myint
            ENCRYPTION=(MASTER_KEY = 'eSxX0jzYfIamtnBKOEOwq80Au6NbSgPH5r4BDDwOaO8=')
            FILE_FORMAT = (FORMAT_NAME = my_csv_format);"""
        result = parse(sql)
        expected = {"copy": {
            "encryption": {"master_key": {"literal": "eSxX0jzYfIamtnBKOEOwq80Au6NbSgPH5r4BDDwOaO8="}},
            "file_format": {"format_name": "my_csv_format"},
            "from": "s3://mybucket/data/files",
            "into": "mytable",
            "storage_integration": "myint",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copy6(self):
        sql = """COPY INTO mytable
            FROM s3://mybucket/data/files
            CREDENTIALS=(AWS_KEY_ID='$AWS_ACCESS_KEY_ID' AWS_SECRET_KEY='$AWS_SECRET_ACCESS_KEY')
            ENCRYPTION=(MASTER_KEY = 'eSxX0jzYfIamtnBKOEOwq80Au6NbSgPH5r4BDDwOaO8=')
            FILE_FORMAT = (FORMAT_NAME = my_csv_format);"""
        result = parse(sql)
        expected = {"copy": {
            "credentials": {
                "aws_key_id": {"literal": "$AWS_ACCESS_KEY_ID"},
                "aws_secret_key": {"literal": "$AWS_SECRET_ACCESS_KEY"},
            },
            "encryption": {"master_key": {"literal": "eSxX0jzYfIamtnBKOEOwq80Au6NbSgPH5r4BDDwOaO8="}},
            "file_format": {"format_name": "my_csv_format"},
            "from": "s3://mybucket/data/files",
            "into": "mytable",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copy7(self):
        sql = """COPY INTO mytable
            FROM 'gcs://mybucket/data/files'
            STORAGE_INTEGRATION = myint
            FILE_FORMAT = (FORMAT_NAME = my_csv_format);"""
        result = parse(sql)
        expected = {"copy": {
            "file_format": {"format_name": "my_csv_format"},
            "from": {"literal": "gcs://mybucket/data/files"},
            "into": "mytable",
            "storage_integration": "myint",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copy8(self):
        sql = """COPY INTO mytable
            FROM 'azure://myaccount.blob.core.windows.net/data/files'
            STORAGE_INTEGRATION = myint
            ENCRYPTION=(TYPE='AZURE_CSE' MASTER_KEY = 'kPxX0jzYfIamtnJEUTHwq80Au6NbSgPH5r4BDDwOaO8=')
            FILE_FORMAT = (FORMAT_NAME = my_csv_format);"""
        result = parse(sql)
        expected = {"copy": {
            "encryption": {
                "master_key": {"literal": "kPxX0jzYfIamtnJEUTHwq80Au6NbSgPH5r4BDDwOaO8="},
                "type": {"literal": "AZURE_CSE"},
            },
            "file_format": {"format_name": "my_csv_format"},
            "from": {"literal": "azure://myaccount.blob.core.windows.net/data/files"},
            "into": "mytable",
            "storage_integration": "myint",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copy9(self):
        sql = """COPY INTO mytable
            FROM 'azure://myaccount.blob.core.windows.net/mycontainer/data/files'
            CREDENTIALS=(AZURE_SAS_TOKEN='?sv=2016-05-31&ss=b&srt=sco&sp=rwdl&se=2018-06-27T10:05:50Z&st=2017-06-27T02:05:50Z&spr=https,http&sig=bgqQwoXwxzuD2GJfagRg7VOS8hzNr3QLT7rhS8OFRLQ%3D')
            ENCRYPTION=(TYPE='AZURE_CSE' MASTER_KEY = 'kPxX0jzYfIamtnJEUTHwq80Au6NbSgPH5r4BDDwOaO8=')
            FILE_FORMAT = (FORMAT_NAME = my_csv_format);"""
        result = parse(sql)
        expected = {"copy": {
            "credentials": {"azure_sas_token": {
                "literal": "?sv=2016-05-31&ss=b&srt=sco&sp=rwdl&se=2018-06-27T10:05:50Z&st=2017-06-27T02:05:50Z&spr=https,http&sig=bgqQwoXwxzuD2GJfagRg7VOS8hzNr3QLT7rhS8OFRLQ%3D"
            }},
            "encryption": {
                "master_key": {"literal": "kPxX0jzYfIamtnJEUTHwq80Au6NbSgPH5r4BDDwOaO8="},
                "type": {"literal": "AZURE_CSE"},
            },
            "file_format": {"format_name": "my_csv_format"},
            "from": {"literal": "azure://myaccount.blob.core.windows.net/mycontainer/data/files"},
            "into": "mytable",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyA(self):
        sql = """COPY INTO mytable
            FILE_FORMAT = (TYPE = 'CSV')
            PATTERN='.*/.*/.*[.]csv[.]gz';"""
        result = parse(sql)
        expected = {"copy": {
            "file_format": {"type": {"literal": "CSV"}},
            "into": "mytable",
            "pattern": {"literal": ".*/.*/.*[.]csv[.]gz"},
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyB(self):
        sql = """COPY INTO mytable
            FILE_FORMAT = (FORMAT_NAME = myformat)
            PATTERN='.*sales.*[.]csv';"""
        result = parse(sql)
        expected = {"copy": {
            "file_format": {"format_name": "myformat"},
            "into": "mytable",
            "pattern": {"literal": ".*sales.*[.]csv"},
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyC(self):
        sql = """COPY INTO load1 FROM @%load1/data1/
            FILES=('test1.csv', 'test2.csv');"""
        result = parse(sql)
        expected = {"copy": {
            "from": "@%load1/data1/",
            "into": "load1",
            "files": {"literal": ["test1.csv", "test2.csv"]},
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyD(self):
        sql = """COPY INTO load1 FROM @%load1/data1/
            FILES=('test1.csv', 'test2.csv')
            FORCE=TRUE;"""
        result = parse(sql)
        expected = {"copy": {
            "files": {"literal": ["test1.csv", "test2.csv"]},
            "force": True,
            "from": "@%load1/data1/",
            "into": "load1",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyE(self):
        sql = """COPY INTO @%orderstiny/result/data_
        FROM orderstiny FILE_FORMAT = (FORMAT_NAME ='myformat' COMPRESSION='GZIP');"""
        result = parse(sql)
        expected = {"copy": {
            "file_format": {"compression": {"literal": "GZIP"}, "format_name": {"literal": "myformat"}},
            "from": "orderstiny",
            "into": "@%orderstiny/result/data_",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyF(self):
        sql = """COPY INTO @my_stage/result/data_ FROM (SELECT * FROM orderstiny)
            file_format=(format_name='myformat' compression='gzip');"""
        result = parse(sql)
        expected = {"copy": {
            "file_format": {"compression": {"literal": "gzip"}, "format_name": {"literal": "myformat"}},
            "from": {"from": "orderstiny", "select": {"all_columns": {}}},
            "into": "@my_stage/result/data_",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyG(self):
        sql = """COPY INTO 's3://mybucket/unload/'
            FROM mytable
            STORAGE_INTEGRATION = myint
            FILE_FORMAT = (FORMAT_NAME = my_csv_format);"""
        result = parse(sql)
        expected = {"copy": {
            "file_format": {"format_name": "my_csv_format"},
            "from": "mytable",
            "into": {"literal": "s3://mybucket/unload/"},
            "storage_integration": "myint",
        }}

        self.assertEqual(result, expected)

    def test_issue_119_copyH(self):
        sql = """COPY INTO 's3://mybucket/unload/'
            FROM mytable
            CREDENTIALS = (AWS_KEY_ID='xxxx' AWS_SECRET_KEY='xxxxx' AWS_TOKEN='xxxxxx')
            FILE_FORMAT = (FORMAT_NAME = my_csv_format);"""
        result = parse(sql)
        expected = {"copy": {
            "credentials": {
                "aws_key_id": {"literal": "xxxx"},
                "aws_secret_key": {"literal": "xxxxx"},
                "aws_token": {"literal": "xxxxxx"},
            },
            "file_format": {"format_name": "my_csv_format"},
            "from": "mytable",
            "into": {"literal": "s3://mybucket/unload/"},
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyI(self):
        sql = """COPY INTO 'gcs://mybucket/unload/'
            FROM mytable
            STORAGE_INTEGRATION = myint
            FILE_FORMAT = (FORMAT_NAME = my_csv_format);"""
        result = parse(sql)
        expected = {"copy": {
            "file_format": {"format_name": "my_csv_format"},
            "from": "mytable",
            "into": {"literal": "gcs://mybucket/unload/"},
            "storage_integration": "myint",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyJ(self):
        sql = """COPY INTO 'azure://myaccount.blob.core.windows.net/unload/'
            FROM mytable
            STORAGE_INTEGRATION = myint
            FILE_FORMAT = (FORMAT_NAME = my_csv_format);"""

        result = parse(sql)
        expected = {"copy": {
            "file_format": {"format_name": "my_csv_format"},
            "from": "mytable",
            "into": {"literal": "azure://myaccount.blob.core.windows.net/unload/"},
            "storage_integration": "myint",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyK(self):
        sql = """COPY INTO 'azure://myaccount.blob.core.windows.net/mycontainer/unload/'
            FROM mytable
            CREDENTIALS=(AZURE_SAS_TOKEN='xxxx')
            FILE_FORMAT = (FORMAT_NAME = my_csv_format);"""

        result = parse(sql)
        expected = {"copy": {
            "credentials": {"azure_sas_token": {"literal": "xxxx"}},
            "file_format": {"format_name": "my_csv_format"},
            "from": "mytable",
            "into": {"literal": "azure://myaccount.blob.core.windows.net/mycontainer/unload/"},
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyL(self):
        sql = """COPY INTO @%t1
            FROM t1
            PARTITION BY ('date=' || to_varchar(dt, 'YYYY-MM-DD') || '/hour=' || to_varchar(date_part(hour, ts))) -- Concatenate labels and column values to output meaningful filenames
            FILE_FORMAT = (TYPE=parquet)
            MAX_FILE_SIZE = 32000000
            HEADER=true;"""
        result = parse(sql)
        expected = {"copy": {
            "file_format": {"type": "parquet"},
            "from": "t1",
            "header": True,
            "into": "@%t1",
            "max_file_size": 32000000,
            "partition_by": {"concat": [
                {"literal": "date="},
                {"to_varchar": ["dt", {"literal": "YYYY-MM-DD"}]},
                {"literal": "/hour="},
                {"to_varchar": {"date_part": ["hour", "ts"]}},
            ]},
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyM(self):
        sql = """COPY INTO @~ FROM HOME_SALES
            FILE_FORMAT = (TYPE = csv NULL_IF = ('NULL', 'null') EMPTY_FIELD_AS_NULL = false);"""
        result = parse(sql)
        expected = {"copy": {
            "file_format": {"empty_field_as_null": False, "null_if": {"literal": ["NULL", "null"]}, "type": "csv"},
            "from": "HOME_SALES",
            "into": "@~",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyN(self):
        sql = """copy into @~ from HOME_SALES
            single = true;"""
        result = parse(sql)
        expected = {"copy": {"from": "HOME_SALES", "into": "@~", "single": True}}
        self.assertEqual(result, expected)

    def test_issue_119_copyO(self):
        sql = """COPY INTO @%t1
            FROM t1
            FILE_FORMAT=(TYPE=parquet)
            INCLUDE_QUERY_ID=true;"""
        result = parse(sql)
        expected = {"copy": {
            "file_format": {"type": "parquet"},
            "from": "t1",
            "include_query_id": True,
            "into": "@%t1",
        }}
        self.assertEqual(result, expected)

    def test_issue_119_copyP(self):
        sql = """COPY INTO @my_stage
            FROM (SELECT * FROM orderstiny LIMIT 5)
            VALIDATION_MODE='RETURN_ROWS';"""
        result = parse(sql)
        expected = {"copy": {
            "from": {"from": "orderstiny", "limit": 5, "select": {"all_columns": {}}},
            "into": "@my_stage",
            "validation_mode": {"literal": "RETURN_ROWS"},
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_table1(self):
        sql = """ALTER TABLE t1 RENAME TO tt1;"""
        result = parse(sql)
        expected = {"alter": {"rename_to": "tt1", "table": "t1"}}
        self.assertEqual(result, expected)

    def test_issue_120_alter_table2(self):
        sql = """ALTER TABLE t1 SWAP WITH t2;"""
        result = parse(sql)
        expected = {"alter": {"swap_with": "t2", "table": "t1"}}
        self.assertEqual(result, expected)

    def test_issue_120_alter_table3(self):
        sql = """ALTER TABLE t1 ADD COLUMN a2 number;"""
        result = parse(sql)
        expected = {"alter": {"add": {"column": {"name": "a2", "type": {"number": {}}}}, "table": "t1"}}
        self.assertEqual(result, expected)

    def test_issue_120_alter_table4(self):
        sql = """ALTER TABLE t1 ADD COLUMN a3 number NOT NULL;"""
        result = parse(sql)
        expected = {"alter": {
            "add": {"column": {"name": "a3", "nullable": False, "type": {"number": {}}}},
            "table": "t1",
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_table5(self):
        sql = """ALTER TABLE t1 ADD COLUMN a4 number DEFAULT 0 NOT NULL;"""
        result = parse(sql)
        expected = {"alter": {
            "add": {"column": {"default": 0, "name": "a4", "nullable": False, "type": {"number": {}}}},
            "table": "t1",
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_table6(self):
        sql = """ALTER TABLE t1 RENAME COLUMN a1 TO b1;"""
        result = parse(sql)
        expected = {"alter": {"rename": {"column": {"name": "a1", "to": "b1"}}, "table": "t1"}}
        self.assertEqual(result, expected)

    def test_issue_120_alter_table7(self):
        sql = """ALTER TABLE t1 DROP COLUMN a2;"""
        result = parse(sql)
        expected = {"alter": {"drop": {"column": "a2"}, "table": "t1"}}
        self.assertEqual(result, expected)

    def test_issue_120_alter_table8(self):
        # VIRTUAL COLUMN a1 = CAST(value as varchar)
        sql = """ALTER TABLE exttable1 ADD COLUMN a1 varchar AS (value:a1::varchar);"""
        result = parse(sql)
        expected = {"alter": {
            "add": {"column": {
                "name": "a1",
                "type": {"varchar": {}},
                "value": {"cast": [{"get": ["value", {"literal": "a1"}]}, {"varchar": {}}]},
            }},
            "table": "exttable1",
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_table9(self):
        sql = """ALTER TABLE t1 CLUSTER BY (date, id);"""
        result = parse(sql)
        expected = {"alter": {"cluster_by": ["date", "id"], "table": "t1"}}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableA(self):
        sql = """alter table t1 add row access policy rap_t1 on (empl_id);"""
        result = parse(sql)
        expected = {"alter": {"add": {"row_access_policy": {"on": "empl_id", "policy": "rap_t1"}}, "table": "t1"}}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableB(self):
        sql = """alter table t1
            add row access policy rap_test2 on (cost, item);"""
        result = parse(sql)
        expected = {"alter": {
            "add": {"row_access_policy": {"on": ["cost", "item"], "policy": "rap_test2"}},
            "table": "t1",
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableC(self):
        sql = """alter table t1 drop row access policy rap_v1;"""
        result = parse(sql)
        expected = {"alter": {"drop": {"row_access_policy": "rap_v1"}, "table": "t1"}}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableD(self):
        sql = """alter table t1
            drop row access policy rap_t1_version_1,
            add row access policy rap_t1_version_2 on (empl_id);"""
        result = parse(sql)
        expected = {"alter": {
            "add": {"row_access_policy": {"on": "empl_id", "policy": "rap_t1_version_2"}},
            "drop": {"row_access_policy": "rap_t1_version_1"},
            "table": "t1",
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableE(self):
        sql = """ALTER TABLE table1
            ADD COLUMN col2 VARCHAR NOT NULL;"""
        result = parse(sql)
        expected = {"alter": {
            "add": {"column": {"name": "col2", "nullable": False, "type": {"varchar": {}}}},
            "table": "table1",
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableF(self):
        sql = """ALTER TABLE table1
            ADD COLUMN col3 VARCHAR NOT NULL CONSTRAINT uniq_col3 UNIQUE NOT ENFORCED;"""
        result = parse(sql)
        expected = {"alter": {
            "add": {
                "column": {"name": "col3", "nullable": False, "type": {"varchar": {}}},
                "constraint": {"name": "uniq_col3", "enforced": False, "unique": True},
            },
            "table": "table1",
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableG(self):
        sql = """ALTER TABLE t1 ALTER COLUMN c1 DROP NOT NULL;"""
        result = parse(sql)
        expected = {"alter": {"modify": {"drop": {"nullable": False}, "name": "c1"}, "table": "t1"}}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableH(self):
        sql = """ALTER TABLE t1 MODIFY c2 DROP DEFAULT, c3 SET DEFAULT seq5.nextval ;"""
        result = parse(sql)
        expected = {"alter": {
            "modify": [{"drop": "default", "name": "c2"}, {"name": "c3", "set": {"default": "seq5.nextval"}}],
            "table": "t1",
        }}

        self.assertEqual(result, expected)

    def test_issue_120_alter_tableI(self):
        sql = """ALTER TABLE t1 ALTER c4 SET DATA TYPE VARCHAR(50), COLUMN c4 DROP DEFAULT;"""
        result = parse(sql)
        expected = {"alter": {
            "modify": [{"name": "c4", "type": {"varchar": 50}}, {"drop": "default", "name": "c4"}],
            "table": "t1",
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableJ(self):
        sql = """ALTER TABLE t1 ALTER c5 COMMENT '50 character column';"""
        result = parse(sql)
        expected = {"alter": {"modify": {"comment": {"literal": "50 character column"}, "name": "c5"}, "table": "t1"}}

        self.assertEqual(result, expected)

    def test_issue_120_alter_tableK(self):
        sql = """ALTER TABLE t1 ALTER (
            c1 DROP NOT NULL,
            c5 COMMENT '50 character column',
            c4 TYPE VARCHAR(50),
            c2 DROP DEFAULT,
            COLUMN c4 DROP DEFAULT,
            COLUMN c3 SET DEFAULT seq5.nextval
            );"""
        result = parse(sql)
        expected = {"alter": {
            "table": "t1",
            "modify": [
                {"name": "c1", "drop": {"nullable": False}},
                {"name": "c5", "comment": {"literal": "50 character column"}},
                {"name": "c4", "type": {"varchar": 50}},
                {"name": "c2", "drop": "default"},
                {"name": "c4", "drop": "default"},
                {"name": "c3", "set": {"default": "seq5.nextval"}},
            ],
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableL(self):
        sql = """ALTER TABLE empl_info MODIFY COLUMN empl_id SET MASKING POLICY mask_empl_id;"""
        result = parse(sql)
        expected = {"alter": {
            "modify": {"name": "empl_id", "set": {"masking_policy": "mask_empl_id"}},
            "table": "empl_info",
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableM(self):
        sql = """ALTER TABLE empl_info MODIFY
            COLUMN empl_id SET MASKING POLICY mask_empl_id
            , COLUMN empl_dob SET MASKING POLICY mask_empl_dob"""
        result = parse(sql)
        expected = {"alter": {
            "table": "empl_info",
            "modify": [
                {"name": "empl_id", "set": {"masking_policy": "mask_empl_id"}},
                {"name": "empl_dob", "set": {"masking_policy": "mask_empl_dob"}},
            ],
        }}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableN(self):
        sql = """ALTER TABLE empl_info modify column empl_id unset masking policy;"""
        result = parse(sql)
        expected = {"alter": {"modify": {"name": "empl_id", "unset": "masking_policy"}, "table": "empl_info"}}
        self.assertEqual(result, expected)

    def test_issue_120_alter_tableO(self):
        sql = """ALTER TABLE empl_info MODIFY
            COLUMN empl_id UNSET MASKING POLICY
            , COLUMN empl_dob UNSET MASKING POLICY"""
        result = parse(sql)
        expected = {"alter": {
            "modify": [
                {"name": "empl_id", "unset": "masking_policy"},
                {"name": "empl_dob", "unset": "masking_policy"},
            ],
            "table": "empl_info",
        }}
        self.assertEqual(result, expected)

    def test_issue_124_overwrite(self):
        sql = """COPY INTO '@my_stage/path'
        FROM my_schema.my_table
        OVERWRITE = TRUE"""
        result = parse(sql)
        expected = {"copy": {"from": "my_schema.my_table", "into": {"literal": "@my_stage/path"}, "overwrite": True}}
        self.assertEqual(result, expected)

    def test_issue_201_create_table_cluster_key(self):
        sql = """CREATE TABLE foo(a varchar(10)) CLUSTER BY ( a )"""
        result = parse(sql)
        expected = {"create table": {
            "columns": {"name": "a", "type": {"varchar": 10}},
            "name": "foo",
            "cluster_by": "a",
        }}
        self.assertEqual(result, expected)

    def test_issue_201_create_table_cluster_key_composite(self):
        sql = """CREATE TABLE foo(a varchar(10), b int) CLUSTER BY ( a, b )"""
        result = parse(sql)
        expected = {"create table": {
            "columns": [{"name": "a", "type": {"varchar": 10}}, {"name": "b", "type": {"int": {}}}],
            "name": "foo",
            "cluster_by": ["a", "b"],
        }}
        self.assertEqual(result, expected)

    def test_issue_222(self):
        sql = """WITH Produce AS (
          SELECT 'Kale' as product, 51 as Q1 UNION ALL
          SELECT 'Kale' as product, 10 UNION ALL
          SELECT 'Apple', 77)
        SELECT sum(Q1) OVER (item_window) AS sum_Q1
        FROM Produce
        WINDOW item_window AS (
          PARTITION BY product
          )"""
        result = parse(sql)
        expected = {
            "select": {"name": "sum_Q1", "over": "item_window", "value": {"sum": "Q1"}},
            "from": "Produce",
            "with": {
                "name": "Produce",
                "value": {"union_all": [
                    {"select": [{"name": "product", "value": {"literal": "Kale"}}, {"name": "Q1", "value": 51}]},
                    {"select": [{"name": "product", "value": {"literal": "Kale"}}, {"value": 10}]},
                    {"select": [{"value": {"literal": "Apple"}}, {"value": 77}]},
                ]},
            },
            "window": {"name": "item_window", "value": {"partitionby": "product"}},
        }
        self.assertEqual(result, expected)
