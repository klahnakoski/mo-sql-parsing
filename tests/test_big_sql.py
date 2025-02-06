# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import json
from unittest import TestCase, skip

from mo_json import value2json
from mo_parsing.debug import Debugger
from mo_times import Timer

from mo_sql_parsing import parse


class TestBigSql(TestCase):
    # @skip("too slow")
    def test_large_expression(self):
        # too slow because the faster() look-ahead can not use regexs
        # specifically, the use of a number in front of an identifier without space
        #    with scale_* => 0.9sec
        # without scale_* => 1.1sec
        #
        # also, extra checks for prefix operators
        #
        # snagged from sqlglot under the mit license
        # https://github.com/tobymao/sqlglot/blob/6294f9e6d08111c6088f5ed9846e7a64f7724801/benchmarks/bench.py#L61
        crazy = "SELECT 1+"
        crazy += "+".join(str(i) for i in range(500))
        crazy += " AS a, 2*"
        crazy += "*".join(str(i) for i in range(500))
        crazy += " AS b FROM x"
        try:
            result = parse("select 1")
        except Exception:
            pass
        with Timer("parse long expression"):
            result = parse(crazy)

    def test_issue_103b(self):
        #        0         1         2         3         4         5         6         7         8         9
        #        012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        sql = """SELECT G.ITEM_ID AS "ITEM_ID", fn_get_dimension_by_grcom (H.BU_COD, G.ITEM_ID) AS "DESCRIPTION", trim(G.EAN11) "EANCODE", trim(DECODE (G.MATNR_ORIG_B2F, NULL, DECODE (G.MATNR_ORIG, NULL, G.MATNR, G.MATNR_ORIG), G.MATNR_ORIG_B2F)) AS "CODICE_PRODOTTO", DECODE (H.BRAND, 'BF GOODRICH', 'BFGOODRICH', H.BRAND) AS "BRAND_ID", H.BRAND AS "XBRAND", H.MARKET5 AS "MKT_ID", m.MC_COUNTRY_CODE AS "COUNTRY_CODE", H.BU_COD AS "GRCOM", H.DATE_FROM AS "PRICELIST_DATE", H.CURRENCY AS "CURRENCY_ID", K.CR_DESCRIPTION AS "CURRENCY_DESC", K.CR_DESCRIPTION AS "CURRENCY_SHORT_DESC", G.PATTERN AS "BTS_ID", P.PATTERN AS "PATTERN_SHORT_DESC", trim(G.SERIES) AS "SERIE", trim(G.WIDTH) AS "CORDA", trim(G.RIM) AS "CALETTAMENTO", G.STRUTTURA AS "STRUTTURA", DECODE (IS_NUMBER (G.WIDTH), 0, 0, TO_NUMBER (G.WIDTH)) AS "CORDA_NOM", DECODE (IS_NUMBER (G.SERIES), 0, 0, TO_NUMBER (G.SERIES)) AS "SERIE_NOM", 0 AS "STRUTTURA_NOM", DECODE (IS_NUMBER (G.RIM), 0, 0, TO_NUMBER (G.RIM)) AS "CALETTAMENTO_NOM", trim(G.LOADIN1) AS "LOAD_INDEX", trim(DECODE (TRIM (G.LOADIN2), '', NULL, TRIM (G.LOADIN2))) AS "LOAD_INDEX_1", trim(G.EXTRA_LOAD_FLAG) AS "EXTRA_LOAD_INDEX", G.RUNFLAT_FLAG AS "RUNFLAT_ID", DECODE (TRIM (G.OEMARK), '', NULL, TRIM (G.OEMARK)) AS "OE_MARK", trim(G.SPEEDIN1) AS "SPEED_INDEX", trim(DECODE (TRIM (G.SPEEDIN2), '', NULL, TRIM (G.SPEEDIN2))) AS "SPEED_INDEX_1", trim(G.CODE_MKS) AS "CODE_MKS", G.DESCR_MKS AS "MKS", D.PRICE AS "GROSS_PRICE", trim(fn_get_dimension_loadindex (g.item_id)) AS "DESCR_LOADINDEX", trim(fn_get_dimension_speedindex (g.item_id)) AS "DESCR_SPEEDINDEX", DECODE (TRIM (G.LOADIN1DB), '', NULL, TRIM (G.LOADIN1DB)) AS "LOADINDEX1DOUBLEMOUNT", DECODE (TRIM (G.LOADIN2DB), '', NULL, TRIM (G.LOADIN2DB)) AS "LOADINDEX2DOUBLEMOUNT", DECODE (TRIM (G.NOISECLASS), '', NULL, TRIM (G.NOISECLASS)) AS "NOISECLASS", DECODE (G.ARTICLEGROUPCODE, '01', 'Tyre', '02', 'Rim', NULL) AS "ARTICLEGROUP", G.ARTICLEGROUPCODE AS "ARTICLEGROUPCODE", DECODE (IS_NUMBER (G.DEPTH), 1, G.DEPTH, NULL) AS "ORIGINALTREADDEPTH", DECODE (IS_NUMBER (G.WEIGHT), 1, TO_NUMBER (G.WEIGHT) * 1000, NULL) AS "WEIGHT", DECODE (g.pncs, 'Yes', 1, 'No', 0, NULL) AS "PNCS", DECODE (g.sealind, 'Yes', 1, 'No', 0, NULL) AS "SELFSEALING", DECODE (g.sealind, 'Yes', g.RUNFLAT_FLAG_SEALIND, NULL) AS "SELFSEALINGINDICATOR", DECODE (g.extra_load, 'Yes', 1, 'No', 0, NULL) AS "EXTRA_LOAD", g.application_code AS "APPLICATION_CODE", NULL AS "PRODUCTSEGMENT", DECODE (g.application_code, 'F1', 'FittedUnitCar', 'F2', 'FittedUnitVan', 'F9', 'FittedUnitSuv', '01', 'Car', '02', 'Van', '03', 'Truck', '04', 'EM', '05', 'AS', '06', 'Industry', '08', 'Moto', '09', 'SUV', NULL) AS "APPLICATION", DECODE (g.SNOWFLAG, 'Yes', 1, 'No', 0, NULL) AS "SNOWFLAG", DECODE (g.RUNFLAT, 'Yes', 1, 'No', 0, NULL) AS "RUNFLAT", DECODE (TRIM (g.NOISE_PERFORMANCE), '', NULL, TRIM (G.NOISE_PERFORMANCE)) AS "NOISE_PERFORMANCE", DECODE (TRIM (g.rollres), '', NULL, TRIM (G.rollres)) AS "ROLLRES", DECODE (TRIM (g.wetgrip), '', NULL, TRIM (G.wetgrip)) AS "WETGRIP", g.MANUFACTURER AS "MANUFACTURER", DECODE (DECODE (IS_NUMBER (g.season), 1, TO_NUMBER (g.season), 0), 1, 'summer', 2, 'winter', 10, 'allseasons', NULL) AS "SEASONALITY" FROM DIM_CURRENCY k, P2_PATTERN_ALL p, P2_MATERIAL_ALL g, DW.DIM_MARKET_CHANNEL m, PRLST_DETAIL d, (SELECT H1.PRICELIST_ID, H1.BRAND, H1.BU_COD, H1.MARKET5, H1.DATE_FROM, H1.CURRENCY FROM PRCLST_HEADER h1, LOOKUP_BRAND b1 WHERE H1.ENABLE_VIEWING_B2F = 1 AND (H1.BRAND, H1.BU_COD, H1.MARKET5, H1.DATE_FROM) IN ( SELECT H2.BRAND, H2.BU_COD, H2.MARKET5, MAX (H2.DATE_FROM) FROM PRCLST_HEADER h2 WHERE H2.BU_COD = 'CAR' AND H2.ENABLE_VIEWING_B2F = 1 GROUP BY H2.BRAND, H2.BU_COD, H2.MARKET5) AND H1.BRAND = B1.BRAND) h WHERE h.currency = K.CR_COD_CURRENCY_SAP AND h.pricelist_id = D.PRICELIST_ID AND H.BRAND = G.BRCONA AND D.IPCODE = G.MATNR AND P.BRAND = G.BRCONA AND upper(P.PATTERN) = upper(G.PATTERN) AND h.market5 = m.MARKET_CHANNEL_CODE AND G.IS_USER = 1 AND (G.BRCONA, G.MATNR) NOT IN (SELECT C.BRCONA, C.MATNR FROM P2_MAT_USER_CONFLICTS c WHERE C.LAST_ACTION IN (21)) ORDER BY G.ITEM_ID"""
        result = parse(sql)
        expected = json.loads(
            """{"select": [{"value": "G.ITEM_ID", "name": "ITEM_ID"}, {"value": {"fn_get_dimension_by_grcom": ["H.BU_COD", "G.ITEM_ID"]}, "name": "DESCRIPTION"}, {"value": {"trim": "G.EAN11"}, "name": "EANCODE"}, {"value": {"trim": {"decode": ["G.MATNR_ORIG_B2F", {"null":{}}, {"decode": ["G.MATNR_ORIG", {"null":{}}, "G.MATNR", "G.MATNR_ORIG"]}, "G.MATNR_ORIG_B2F"]}}, "name": "CODICE_PRODOTTO"}, {"value": {"decode": ["H.BRAND", {"literal": "BF GOODRICH"}, {"literal": "BFGOODRICH"}, "H.BRAND"]}, "name": "BRAND_ID"}, {"value": "H.BRAND", "name": "XBRAND"}, {"value": "H.MARKET5", "name": "MKT_ID"}, {"value": "m.MC_COUNTRY_CODE", "name": "COUNTRY_CODE"}, {"value": "H.BU_COD", "name": "GRCOM"}, {"value": "H.DATE_FROM", "name": "PRICELIST_DATE"}, {"value": "H.CURRENCY", "name": "CURRENCY_ID"}, {"value": "K.CR_DESCRIPTION", "name": "CURRENCY_DESC"}, {"value": "K.CR_DESCRIPTION", "name": "CURRENCY_SHORT_DESC"}, {"value": "G.PATTERN", "name": "BTS_ID"}, {"value": "P.PATTERN", "name": "PATTERN_SHORT_DESC"}, {"value": {"trim": "G.SERIES"}, "name": "SERIE"}, {"value": {"trim": "G.WIDTH"}, "name": "CORDA"}, {"value": {"trim": "G.RIM"}, "name": "CALETTAMENTO"}, {"value": "G.STRUTTURA", "name": "STRUTTURA"}, {"value": {"decode": [{"is_number": "G.WIDTH"}, 0, 0, {"to_number": "G.WIDTH"}]}, "name": "CORDA_NOM"}, {"value": {"decode": [{"is_number": "G.SERIES"}, 0, 0, {"to_number": "G.SERIES"}]}, "name": "SERIE_NOM"}, {"value": 0, "name": "STRUTTURA_NOM"}, {"value": {"decode": [{"is_number": "G.RIM"}, 0, 0, {"to_number": "G.RIM"}]}, "name": "CALETTAMENTO_NOM"}, {"value": {"trim": "G.LOADIN1"}, "name": "LOAD_INDEX"}, {"value": {"trim": {"decode": [{"trim": "G.LOADIN2"}, {"literal": ""}, {"null":{}}, {"trim": "G.LOADIN2"}]}}, "name": "LOAD_INDEX_1"}, {"value": {"trim": "G.EXTRA_LOAD_FLAG"}, "name": "EXTRA_LOAD_INDEX"}, {"value": "G.RUNFLAT_FLAG", "name": "RUNFLAT_ID"}, {"value": {"decode": [{"trim": "G.OEMARK"}, {"literal": ""}, {"null":{}}, {"trim": "G.OEMARK"}]}, "name": "OE_MARK"}, {"value": {"trim": "G.SPEEDIN1"}, "name": "SPEED_INDEX"}, {"value": {"trim": {"decode": [{"trim": "G.SPEEDIN2"}, {"literal": ""}, {"null":{}}, {"trim": "G.SPEEDIN2"}]}}, "name": "SPEED_INDEX_1"}, {"value": {"trim": "G.CODE_MKS"}, "name": "CODE_MKS"}, {"value": "G.DESCR_MKS", "name": "MKS"}, {"value": "D.PRICE", "name": "GROSS_PRICE"}, {"value": {"trim": {"fn_get_dimension_loadindex": "g.item_id"}}, "name": "DESCR_LOADINDEX"}, {"value": {"trim": {"fn_get_dimension_speedindex": "g.item_id"}}, "name": "DESCR_SPEEDINDEX"}, {"value": {"decode": [{"trim": "G.LOADIN1DB"}, {"literal": ""}, {"null":{}}, {"trim": "G.LOADIN1DB"}]}, "name": "LOADINDEX1DOUBLEMOUNT"}, {"value": {"decode": [{"trim": "G.LOADIN2DB"}, {"literal": ""}, {"null":{}}, {"trim": "G.LOADIN2DB"}]}, "name": "LOADINDEX2DOUBLEMOUNT"}, {"value": {"decode": [{"trim": "G.NOISECLASS"}, {"literal": ""}, {"null":{}}, {"trim": "G.NOISECLASS"}]}, "name": "NOISECLASS"}, {"value": {"decode": ["G.ARTICLEGROUPCODE", {"literal": "01"}, {"literal": "Tyre"}, {"literal": "02"}, {"literal": "Rim"}, {"null":{}}]}, "name": "ARTICLEGROUP"}, {"value": "G.ARTICLEGROUPCODE", "name": "ARTICLEGROUPCODE"}, {"value": {"decode": [{"is_number": "G.DEPTH"}, 1, "G.DEPTH", {"null":{}}]}, "name": "ORIGINALTREADDEPTH"}, {"value": {"decode": [{"is_number": "G.WEIGHT"}, 1, {"mul": [{"to_number": "G.WEIGHT"}, 1000]}, {"null":{}}]}, "name": "WEIGHT"}, {"value": {"decode": ["g.pncs", {"literal": "Yes"}, 1, {"literal": "No"}, 0, {"null":{}}]}, "name": "PNCS"}, {"value": {"decode": ["g.sealind", {"literal": "Yes"}, 1, {"literal": "No"}, 0, {"null":{}}]}, "name": "SELFSEALING"}, {"value": {"decode": ["g.sealind", {"literal": "Yes"}, "g.RUNFLAT_FLAG_SEALIND", {"null":{}}]}, "name": "SELFSEALINGINDICATOR"}, {"value": {"decode": ["g.extra_load", {"literal": "Yes"}, 1, {"literal": "No"}, 0, {"null":{}}]}, "name": "EXTRA_LOAD"}, {"value": "g.application_code", "name": "APPLICATION_CODE"}, {"name": "PRODUCTSEGMENT", "value":{"null":{}}}, {"value": {"decode": ["g.application_code", {"literal": "F1"}, {"literal": "FittedUnitCar"}, {"literal": "F2"}, {"literal": "FittedUnitVan"}, {"literal": "F9"}, {"literal": "FittedUnitSuv"}, {"literal": "01"}, {"literal": "Car"}, {"literal": "02"}, {"literal": "Van"}, {"literal": "03"}, {"literal": "Truck"}, {"literal": "04"}, {"literal": "EM"}, {"literal": "05"}, {"literal": "AS"}, {"literal": "06"}, {"literal": "Industry"}, {"literal": "08"}, {"literal": "Moto"}, {"literal": "09"}, {"literal": "SUV"}, {"null":{}}]}, "name": "APPLICATION"}, {"value": {"decode": ["g.SNOWFLAG", {"literal": "Yes"}, 1, {"literal": "No"}, 0, {"null":{}}]}, "name": "SNOWFLAG"}, {"value": {"decode": ["g.RUNFLAT", {"literal": "Yes"}, 1, {"literal": "No"}, 0, {"null":{}}]}, "name": "RUNFLAT"}, {"value": {"decode": [{"trim": "g.NOISE_PERFORMANCE"}, {"literal": ""}, {"null":{}}, {"trim": "G.NOISE_PERFORMANCE"}]}, "name": "NOISE_PERFORMANCE"}, {"value": {"decode": [{"trim": "g.rollres"}, {"literal": ""}, {"null":{}}, {"trim": "G.rollres"}]}, "name": "ROLLRES"}, {"value": {"decode": [{"trim": "g.wetgrip"}, {"literal": ""}, {"null":{}}, {"trim": "G.wetgrip"}]}, "name": "WETGRIP"}, {"value": "g.MANUFACTURER", "name": "MANUFACTURER"}, {"value": {"decode": [{"decode": [{"is_number": "g.season"}, 1, {"to_number": "g.season"}, 0]}, 1, {"literal": "summer"}, 2, {"literal": "winter"}, 10, {"literal": "allseasons"}, {"null":{}}]}, "name": "SEASONALITY"}], "from": [{"value": "DIM_CURRENCY", "name": "k"}, {"value": "P2_PATTERN_ALL", "name": "p"}, {"value": "P2_MATERIAL_ALL", "name": "g"}, {"value": "DW.DIM_MARKET_CHANNEL", "name": "m"}, {"value": "PRLST_DETAIL", "name": "d"}, {"value": {"select": [{"value": "H1.PRICELIST_ID"}, {"value": "H1.BRAND"}, {"value": "H1.BU_COD"}, {"value": "H1.MARKET5"}, {"value": "H1.DATE_FROM"}, {"value": "H1.CURRENCY"}], "from": [{"value": "PRCLST_HEADER", "name": "h1"}, {"value": "LOOKUP_BRAND", "name": "b1"}], "where": {"and": [{"eq": ["H1.ENABLE_VIEWING_B2F", 1]}, {"in": [["H1.BRAND", "H1.BU_COD", "H1.MARKET5", "H1.DATE_FROM"], {"select": [{"value": "H2.BRAND"}, {"value": "H2.BU_COD"}, {"value": "H2.MARKET5"}, {"value": {"max": "H2.DATE_FROM"}}], "from": {"value": "PRCLST_HEADER", "name": "h2"}, "where": {"and": [{"eq": ["H2.BU_COD", {"literal": "CAR"}]}, {"eq": ["H2.ENABLE_VIEWING_B2F", 1]}]}, "groupby": [{"value": "H2.BRAND"}, {"value": "H2.BU_COD"}, {"value": "H2.MARKET5"}]}]}, {"eq": ["H1.BRAND", "B1.BRAND"]}]}}, "name": "h"}], "where": {"and": [{"eq": ["h.currency", "K.CR_COD_CURRENCY_SAP"]}, {"eq": ["h.pricelist_id", "D.PRICELIST_ID"]}, {"eq": ["H.BRAND", "G.BRCONA"]}, {"eq": ["D.IPCODE", "G.MATNR"]}, {"eq": ["P.BRAND", "G.BRCONA"]}, {"eq": [{"upper": "P.PATTERN"}, {"upper": "G.PATTERN"}]}, {"eq": ["h.market5", "m.MARKET_CHANNEL_CODE"]}, {"eq": ["G.IS_USER", 1]}, {"nin": [["G.BRCONA", "G.MATNR"], {"select": [{"value": "C.BRCONA"}, {"value": "C.MATNR"}], "from": {"value": "P2_MAT_USER_CONFLICTS", "name": "c"}, "where": {"in": ["C.LAST_ACTION", 21]}}]}]}, "orderby": {"value": "G.ITEM_ID"}}"""
        )
        self.assertEqual(result, expected)

    def test_issue_21_many_with_clauses(self):
        sql = """
            WITH ssr
            AS (
                SELECT s_store_id
                    ,sum(sales_price) AS sales
                    ,sum(profit) AS profit
                    ,sum(return_amt) AS
                RETURNS
                    ,sum(net_loss) AS profit_loss
                FROM (
                    SELECT ss_store_sk AS store_sk
                        ,ss_sold_date_sk AS date_sk
                        ,ss_ext_sales_price AS sales_price
                        ,ss_net_profit AS profit
                        ,cast(0 AS DECIMAL(7, 2)) AS return_amt
                        ,cast(0 AS DECIMAL(7, 2)) AS net_loss
                    FROM store_sales
                    
                    UNION ALL
                    
                    SELECT sr_store_sk AS store_sk
                        ,sr_returned_date_sk AS date_sk
                        ,cast(0 AS DECIMAL(7, 2)) AS sales_price
                        ,cast(0 AS DECIMAL(7, 2)) AS profit
                        ,sr_return_amt AS return_amt
                        ,sr_net_loss AS net_loss
                    FROM store_returns
                    ) salesreturns
                    ,date_dim
                    ,store
                WHERE date_sk = d_date_sk
                    AND d_date BETWEEN cast('1998-08-18' AS DATE)
                        AND dateadd(day, 14, cast('1998-08-18' AS DATE))
                    AND store_sk = s_store_sk
                GROUP BY s_store_id
                )
                ,csr
            AS (
                SELECT cp_catalog_page_id
                    ,sum(sales_price) AS sales
                    ,sum(profit) AS profit
                    ,sum(return_amt) AS
                RETURNS
                    ,sum(net_loss) AS profit_loss
                FROM (
                    SELECT cs_catalog_page_sk AS page_sk
                        ,cs_sold_date_sk AS date_sk
                        ,cs_ext_sales_price AS sales_price
                        ,cs_net_profit AS profit
                        ,cast(0 AS DECIMAL(7, 2)) AS return_amt
                        ,cast(0 AS DECIMAL(7, 2)) AS net_loss
                    FROM catalog_sales
                    
                    UNION ALL
                    
                    SELECT cr_catalog_page_sk AS page_sk
                        ,cr_returned_date_sk AS date_sk
                        ,cast(0 AS DECIMAL(7, 2)) AS sales_price
                        ,cast(0 AS DECIMAL(7, 2)) AS profit
                        ,cr_return_amount AS return_amt
                        ,cr_net_loss AS net_loss
                    FROM catalog_returns
                    ) salesreturns
                    ,date_dim
                    ,catalog_page
                WHERE date_sk = d_date_sk
                    AND d_date BETWEEN cast('1998-08-18' AS DATE)
                        AND dateadd(day, 14, cast('1998-08-18' AS DATE))
                    AND page_sk = cp_catalog_page_sk
                GROUP BY cp_catalog_page_id
                )
                ,wsr
            AS (
                SELECT web_site_id
                    ,sum(sales_price) AS sales
                    ,sum(profit) AS profit
                    ,sum(return_amt) AS
                RETURNS
                    ,sum(net_loss) AS profit_loss
                FROM (
                    SELECT ws_web_site_sk AS wsr_web_site_sk
                        ,ws_sold_date_sk AS date_sk
                        ,ws_ext_sales_price AS sales_price
                        ,ws_net_profit AS profit
                        ,cast(0 AS DECIMAL(7, 2)) AS return_amt
                        ,cast(0 AS DECIMAL(7, 2)) AS net_loss
                    FROM web_sales
                    
                    UNION ALL
                    
                    SELECT ws_web_site_sk AS wsr_web_site_sk
                        ,wr_returned_date_sk AS date_sk
                        ,cast(0 AS DECIMAL(7, 2)) AS sales_price
                        ,cast(0 AS DECIMAL(7, 2)) AS profit
                        ,wr_return_amt AS return_amt
                        ,wr_net_loss AS net_loss
                    FROM web_returns
                    LEFT OUTER JOIN web_sales ON (
                            wr_item_sk = ws_item_sk
                            AND wr_order_number = ws_order_number
                            )
                    ) salesreturns
                    ,date_dim
                    ,web_site
                WHERE date_sk = d_date_sk
                    AND d_date BETWEEN cast('1998-08-18' AS DATE)
                        AND dateadd(day, 14, cast('1998-08-18' AS DATE))
                    AND wsr_web_site_sk = web_site_sk
                GROUP BY web_site_id
                )
            SELECT channel
                ,id
                ,sum(sales) AS sales
                ,sum(RETURNS) AS
            RETURNS
                ,sum(profit) AS profit
            FROM (
                SELECT 'store channel' AS channel
                    ,'store' || s_store_id AS id
                    ,sales
                    ,
                RETURNS
                    ,(profit - profit_loss) AS profit
                FROM ssr
                
                UNION ALL
                
                SELECT 'catalog channel' AS channel
                    ,'catalog_page' || cp_catalog_page_id AS id
                    ,sales
                    ,
                RETURNS
                    ,(profit - profit_loss) AS profit
                FROM csr
                
                UNION ALL
                
                SELECT 'web channel' AS channel
                    ,'web_site' || web_site_id AS id
                    ,sales
                    ,
                RETURNS
                    ,(profit - profit_loss) AS profit
                FROM wsr
                ) x
            GROUP BY rollup(channel, id)
            ORDER BY channel
                ,id limit 100;    
        """

        result = parse(sql)
        expected = {
            "from": {
                "name": "x",
                "value": {"union_all": [
                    {
                        "from": "ssr",
                        "select": [
                            {"name": "channel", "value": {"literal": "store channel"}},
                            {"name": "id", "value": {"concat": [{"literal": "store"}, "s_store_id"]}},
                            {"value": "sales"},
                            {"value": "RETURNS"},
                            {"name": "profit", "value": {"sub": ["profit", "profit_loss"]}},
                        ],
                    },
                    {
                        "from": "csr",
                        "select": [
                            {"name": "channel", "value": {"literal": "catalog channel"}},
                            {"name": "id", "value": {"concat": [{"literal": "catalog_page"}, "cp_catalog_page_id"]}},
                            {"value": "sales"},
                            {"value": "RETURNS"},
                            {"name": "profit", "value": {"sub": ["profit", "profit_loss"]}},
                        ],
                    },
                    {
                        "from": "wsr",
                        "select": [
                            {"name": "channel", "value": {"literal": "web channel"}},
                            {"name": "id", "value": {"concat": [{"literal": "web_site"}, "web_site_id"]}},
                            {"value": "sales"},
                            {"value": "RETURNS"},
                            {"name": "profit", "value": {"sub": ["profit", "profit_loss"]}},
                        ],
                    },
                ]},
            },
            "groupby": {"value": {"rollup": ["channel", "id"]}},
            "limit": 100,
            "orderby": [{"value": "channel"}, {"value": "id"}],
            "select": [
                {"value": "channel"},
                {"value": "id"},
                {"name": "sales", "value": {"sum": "sales"}},
                {"name": "RETURNS", "value": {"sum": "RETURNS"}},
                {"name": "profit", "value": {"sum": "profit"}},
            ],
            "with": [
                {
                    "name": "ssr",
                    "value": {
                        "from": [
                            {
                                "name": "salesreturns",
                                "value": {"union_all": [
                                    {
                                        "from": "store_sales",
                                        "select": [
                                            {"name": "store_sk", "value": "ss_store_sk"},
                                            {"name": "date_sk", "value": "ss_sold_date_sk"},
                                            {"name": "sales_price", "value": "ss_ext_sales_price"},
                                            {"name": "profit", "value": "ss_net_profit"},
                                            {"name": "return_amt", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                            {"name": "net_loss", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                        ],
                                    },
                                    {
                                        "from": "store_returns",
                                        "select": [
                                            {"name": "store_sk", "value": "sr_store_sk"},
                                            {"name": "date_sk", "value": "sr_returned_date_sk"},
                                            {"name": "sales_price", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                            {"name": "profit", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                            {"name": "return_amt", "value": "sr_return_amt"},
                                            {"name": "net_loss", "value": "sr_net_loss"},
                                        ],
                                    },
                                ]},
                            },
                            "date_dim",
                            "store",
                        ],
                        "groupby": {"value": "s_store_id"},
                        "select": [
                            {"value": "s_store_id"},
                            {"name": "sales", "value": {"sum": "sales_price"}},
                            {"name": "profit", "value": {"sum": "profit"}},
                            {"name": "RETURNS", "value": {"sum": "return_amt"}},
                            {"name": "profit_loss", "value": {"sum": "net_loss"}},
                        ],
                        "where": {"and": [
                            {"eq": ["date_sk", "d_date_sk"]},
                            {"between": [
                                "d_date",
                                {"cast": [{"literal": "1998-08-18"}, {"date": {}}]},
                                {"dateadd": ["day", 14, {"cast": [{"literal": "1998-08-18"}, {"date": {}}]}]},
                            ]},
                            {"eq": ["store_sk", "s_store_sk"]},
                        ]},
                    },
                },
                {
                    "name": "csr",
                    "value": {
                        "from": [
                            {
                                "name": "salesreturns",
                                "value": {"union_all": [
                                    {
                                        "from": "catalog_sales",
                                        "select": [
                                            {"name": "page_sk", "value": "cs_catalog_page_sk"},
                                            {"name": "date_sk", "value": "cs_sold_date_sk"},
                                            {"name": "sales_price", "value": "cs_ext_sales_price"},
                                            {"name": "profit", "value": "cs_net_profit"},
                                            {"name": "return_amt", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                            {"name": "net_loss", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                        ],
                                    },
                                    {
                                        "from": "catalog_returns",
                                        "select": [
                                            {"name": "page_sk", "value": "cr_catalog_page_sk"},
                                            {"name": "date_sk", "value": "cr_returned_date_sk"},
                                            {"name": "sales_price", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                            {"name": "profit", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                            {"name": "return_amt", "value": "cr_return_amount"},
                                            {"name": "net_loss", "value": "cr_net_loss"},
                                        ],
                                    },
                                ]},
                            },
                            "date_dim",
                            "catalog_page",
                        ],
                        "groupby": {"value": "cp_catalog_page_id"},
                        "select": [
                            {"value": "cp_catalog_page_id"},
                            {"name": "sales", "value": {"sum": "sales_price"}},
                            {"name": "profit", "value": {"sum": "profit"}},
                            {"name": "RETURNS", "value": {"sum": "return_amt"}},
                            {"name": "profit_loss", "value": {"sum": "net_loss"}},
                        ],
                        "where": {"and": [
                            {"eq": ["date_sk", "d_date_sk"]},
                            {"between": [
                                "d_date",
                                {"cast": [{"literal": "1998-08-18"}, {"date": {}}]},
                                {"dateadd": ["day", 14, {"cast": [{"literal": "1998-08-18"}, {"date": {}}]}]},
                            ]},
                            {"eq": ["page_sk", "cp_catalog_page_sk"]},
                        ]},
                    },
                },
                {
                    "name": "wsr",
                    "value": {
                        "from": [
                            {
                                "name": "salesreturns",
                                "value": {"union_all": [
                                    {
                                        "from": "web_sales",
                                        "select": [
                                            {"name": "wsr_web_site_sk", "value": "ws_web_site_sk"},
                                            {"name": "date_sk", "value": "ws_sold_date_sk"},
                                            {"name": "sales_price", "value": "ws_ext_sales_price"},
                                            {"name": "profit", "value": "ws_net_profit"},
                                            {"name": "return_amt", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                            {"name": "net_loss", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                        ],
                                    },
                                    {
                                        "from": [
                                            "web_returns",
                                            {
                                                "left outer join": "web_sales",
                                                "on": {"and": [
                                                    {"eq": ["wr_item_sk", "ws_item_sk"]},
                                                    {"eq": ["wr_order_number", "ws_order_number"]},
                                                ]},
                                            },
                                        ],
                                        "select": [
                                            {"name": "wsr_web_site_sk", "value": "ws_web_site_sk"},
                                            {"name": "date_sk", "value": "wr_returned_date_sk"},
                                            {"name": "sales_price", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                            {"name": "profit", "value": {"cast": [0, {"decimal": [7, 2]}]}},
                                            {"name": "return_amt", "value": "wr_return_amt"},
                                            {"name": "net_loss", "value": "wr_net_loss"},
                                        ],
                                    },
                                ]},
                            },
                            "date_dim",
                            "web_site",
                        ],
                        "groupby": {"value": "web_site_id"},
                        "select": [
                            {"value": "web_site_id"},
                            {"name": "sales", "value": {"sum": "sales_price"}},
                            {"name": "profit", "value": {"sum": "profit"}},
                            {"name": "RETURNS", "value": {"sum": "return_amt"}},
                            {"name": "profit_loss", "value": {"sum": "net_loss"}},
                        ],
                        "where": {"and": [
                            {"eq": ["date_sk", "d_date_sk"]},
                            {"between": [
                                "d_date",
                                {"cast": [{"literal": "1998-08-18"}, {"date": {}}]},
                                {"dateadd": ["day", 14, {"cast": [{"literal": "1998-08-18"}, {"date": {}}]}]},
                            ]},
                            {"eq": ["wsr_web_site_sk", "web_site_sk"]},
                        ]},
                    },
                },
            ],
        }

        self.assertEqual(result, expected)

    def test_issue144(self):
        sql = """WITH balance AS (
    SELECT
        beyblade_id                                               AS beyblade_id
        ,babala_id                                             AS babala_id
        ,CASE 
            WHEN datinha_marota = \"9999-12-31\" 
            THEN due_date 
            ELSE datinha_marota 
        END                                                     AS age
        ,SUM(hugo_boss)                            AS hugo_boss
        ,SUM(net_dos_milagres)                              AS net_dos_milagres                                  
    FROM `*******************.**********************.********************` mov
    WHERE
        reference_date <= DATE_SUB(_reference_date, INTERVAL 2 DAY)
        AND 
        (datinha_marota > DATE_SUB(_reference_date, INTERVAL 2 DAY) OR datinha_marota IS NULL)
    GROUP BY 1, 2, 3
), balance_settled_to_disregard AS (
    SELECT
        beyblade_id
        ,babala_id
        ,datinha_marota
        ,SUM(hugo_boss)                                        AS hugo_boss
        ,SUM(net_dos_milagres)                                          AS net_dos_milagres
    FROM `*******************.**********************.********************` mov
    WHERE  
        (datinha_marota >= DATE_SUB(_reference_date, INTERVAL 1 DAY)
        AND datinha_marota <= _reference_date)
        AND reference_date <= DATE_SUB(_reference_date, INTERVAL 2 DAY)
    GROUP BY 1, 2, 3
), tpv AS (
    SELECT
        IF(teraband_discreto = 'VISA', 10,
            IF(teraband_discreto = 'MasterCard', 40,
                IF(teraband_discreto = 'Elo', 20,
                    IF(teraband_discreto = 'Hiper / HiperCard', 78,
                        IF(teraband_discreto = 'American Express', 23,
                            IF(teraband_discreto = 'Cabal', 1235, 1234)))))) as beyblade_id
        ,CASE WHEN
            teraband_discreto = 'MasterCard' THEN
                IF(tipinho_maroto_id = 2, 1234, 12354)
            ELSE
                IF(tipinho_maroto_id = 10, 123, 234)
        END AS babala_id
        ,DATE(IF(
            tipinho_maroto_id = 2, 
            DATE_ADD(dia_da_apresentacaozinha, INTERVAL 28+(installment_number-1)*30 DAY), 
            dia_da_apresentacaozinha
        ))                                                                              AS age       
        ,SUM(
        CASE 
            WHEN tx_type = 1 
            THEN +instagram_original 
            ELSE -instagram_original 
        END)                                                                            AS hugo_boss
        ,SUM(
        CASE 
            WHEN tx_type = 1 
            THEN +instagram_original 
            ELSE -instagram_original 
        END) -
        SUM(
        CASE 
            WHEN tx_type = 1 
            THEN +amount 
            ELSE -amount 
        END)                                                                            AS net_dos_milagres
    FROM `*******************.**********************.********************` t
    WHERE
        CASE 
            WHEN tipinho_maroto_id = 1
            THEN (
                CASE 
                    WHEN is_week_day
                    THEN (
                        DATE(dia_da_apresentacaozinha) = _reference_date
                    )
                    ELSE (
                        DATE(dia_da_apresentacaozinha) 
                        BETWEEN 
                        DATE_SUB(_reference_date, INTERVAL 1 DAY) AND
                        _reference_date
                        
                    )
                END 
            )
            ELSE (
                DATE(dia_da_apresentacaozinha) 
                BETWEEN 
                DATE_SUB(_reference_date, INTERVAL 1 DAY) AND
                _reference_date 
            )
        END
    GROUP BY 1, 2, 3
)

SELECT
    stg.reference_date
    ,inst.name                  AS hytofly
    ,st.name                    AS service_type
    ,stg.age
    ,stg.hugo_boss
    ,stg.net_dos_milagres
    ,stg.updated_at
FROM (
    SELECT 
        _reference_date                                                                                     AS reference_date
        ,IFNULL(IFNULL(bal.babala_id, bstd.babala_id), t.babala_id)                       AS babala_id
        ,IFNULL(IFNULL(bal.beyblade_id, bstd.beyblade_id), t.beyblade_id)                          AS beyblade_id
        ,COALESCE(DATE(t.age), DATE(bal.age))                                                               AS age
        ,IFNULL(bal.hugo_boss, 0) - IFNULL(bstd.hugo_boss, 0) + IFNULL(t.hugo_boss, 0)             AS hugo_boss
        ,IFNULL(bal.net_dos_milagres, 0) - IFNULL(bstd.net_dos_milagres, 0) + IFNULL(t.net_dos_milagres, 0)                   AS net_dos_milagres
        ,current_timestamp                                                                                  AS updated_at
    FROM balance bal
    FULL JOIN balance_settled_to_disregard bstd 
        ON DATE(bal.age) = DATE(bstd.datinha_marota)
        AND bal.babala_id = bstd.babala_id
        AND bal.beyblade_id = bstd.beyblade_id
    FULL JOIN tpv t
        ON DATE(bal.age) = DATE(t.age)
        AND bal.babala_id = t.babala_id
        AND bal.beyblade_id = t.beyblade_id
) stg
    JOIN `*******************.**********************.********************` st
        ON st.babala_id = stg.babala_id
    JOIN `*******************.**********************.********************` inst
        ON inst.beyblade_id = stg.beyblade_id
"""
        with Timer("parse big sql"):
            result = parse(sql)
        value2json(result)
        expected = {
            "from": [
                {
                    "name": "stg",
                    "value": {
                        "from": [
                            {"name": "bal", "value": "balance"},
                            {
                                "full join": {"name": "bstd", "value": "balance_settled_to_disregard"},
                                "on": {"and": [
                                    {"eq": [{"date": "bal.age"}, {"date": "bstd.datinha_marota"}]},
                                    {"eq": ["bal.babala_id", "bstd.babala_id"]},
                                    {"eq": ["bal.beyblade_id", "bstd.beyblade_id"]},
                                ]},
                            },
                            {
                                "full join": {"name": "t", "value": "tpv"},
                                "on": {"and": [
                                    {"eq": [{"date": "bal.age"}, {"date": "t.age"}]},
                                    {"eq": ["bal.babala_id", "t.babala_id"]},
                                    {"eq": ["bal.beyblade_id", "t.beyblade_id"]},
                                ]},
                            },
                        ],
                        "select": [
                            {"name": "reference_date", "value": "_reference_date"},
                            {
                                "name": "babala_id",
                                "value": {"ifnull": [{"ifnull": ["bal.babala_id", "bstd.babala_id"]}, "t.babala_id"]},
                            },
                            {
                                "name": "beyblade_id",
                                "value": {"ifnull": [
                                    {"ifnull": ["bal.beyblade_id", "bstd.beyblade_id"]},
                                    "t.beyblade_id",
                                ]},
                            },
                            {"name": "age", "value": {"coalesce": [{"date": "t.age"}, {"date": "bal.age"}]}},
                            {
                                "name": "hugo_boss",
                                "value": {"add": [
                                    {"sub": [{"ifnull": ["bal.hugo_boss", 0]}, {"ifnull": ["bstd.hugo_boss", 0]}]},
                                    {"ifnull": ["t.hugo_boss", 0]},
                                ]},
                            },
                            {
                                "name": "net_dos_milagres",
                                "value": {"add": [
                                    {"sub": [
                                        {"ifnull": ["bal.net_dos_milagres", 0]},
                                        {"ifnull": ["bstd.net_dos_milagres", 0]},
                                    ]},
                                    {"ifnull": ["t.net_dos_milagres", 0]},
                                ]},
                            },
                            {"name": "updated_at", "value": "current_timestamp"},
                        ],
                    },
                },
                {
                    "join": {
                        "name": "st",
                        "value": "*******************..**********************..********************",
                    },
                    "on": {"eq": ["st.babala_id", "stg.babala_id"]},
                },
                {
                    "join": {
                        "name": "inst",
                        "value": "*******************..**********************..********************",
                    },
                    "on": {"eq": ["inst.beyblade_id", "stg.beyblade_id"]},
                },
            ],
            "select": [
                {"value": "stg.reference_date"},
                {"name": "hytofly", "value": "inst.name"},
                {"name": "service_type", "value": "st.name"},
                {"value": "stg.age"},
                {"value": "stg.hugo_boss"},
                {"value": "stg.net_dos_milagres"},
                {"value": "stg.updated_at"},
            ],
            "with": [
                {
                    "name": "balance",
                    "value": {
                        "from": {
                            "name": "mov",
                            "value": "*******************..**********************..********************",
                        },
                        "groupby": [{"value": 1}, {"value": 2}, {"value": 3}],
                        "select": [
                            {"name": "beyblade_id", "value": "beyblade_id"},
                            {"name": "babala_id", "value": "babala_id"},
                            {
                                "name": "age",
                                "value": {"case": [
                                    {"then": "due_date", "when": {"eq": ["datinha_marota", "9999-12-31"]}},
                                    "datinha_marota",
                                ]},
                            },
                            {"name": "hugo_boss", "value": {"sum": "hugo_boss"}},
                            {"name": "net_dos_milagres", "value": {"sum": "net_dos_milagres"}},
                        ],
                        "where": {"and": [
                            {"lte": ["reference_date", {"date_sub": ["_reference_date", {"interval": [2, "day"]}]}]},
                            {"or": [
                                {"gt": [
                                    "datinha_marota",
                                    {"date_sub": ["_reference_date", {"interval": [2, "day"]}]},
                                ]},
                                {"missing": "datinha_marota"},
                            ]},
                        ]},
                    },
                },
                {
                    "name": "balance_settled_to_disregard",
                    "value": {
                        "from": {
                            "name": "mov",
                            "value": "*******************..**********************..********************",
                        },
                        "groupby": [{"value": 1}, {"value": 2}, {"value": 3}],
                        "select": [
                            {"value": "beyblade_id"},
                            {"value": "babala_id"},
                            {"value": "datinha_marota"},
                            {"name": "hugo_boss", "value": {"sum": "hugo_boss"}},
                            {"name": "net_dos_milagres", "value": {"sum": "net_dos_milagres"}},
                        ],
                        "where": {"and": [
                            {"gte": ["datinha_marota", {"date_sub": ["_reference_date", {"interval": [1, "day"]}]}]},
                            {"lte": ["datinha_marota", "_reference_date"]},
                            {"lte": ["reference_date", {"date_sub": ["_reference_date", {"interval": [2, "day"]}]}]},
                        ]},
                    },
                },
                {
                    "name": "tpv",
                    "value": {
                        "from": {
                            "name": "t",
                            "value": "*******************..**********************..********************",
                        },
                        "groupby": [{"value": 1}, {"value": 2}, {"value": 3}],
                        "select": [
                            {
                                "name": "beyblade_id",
                                "value": {"if": [
                                    {"eq": ["teraband_discreto", {"literal": "VISA"}]},
                                    10,
                                    {"if": [
                                        {"eq": ["teraband_discreto", {"literal": "MasterCard"}]},
                                        40,
                                        {"if": [
                                            {"eq": ["teraband_discreto", {"literal": "Elo"}]},
                                            20,
                                            {"if": [
                                                {"eq": ["teraband_discreto", {"literal": "Hiper / HiperCard"}]},
                                                78,
                                                {"if": [
                                                    {"eq": ["teraband_discreto", {"literal": "American Express"}]},
                                                    23,
                                                    {"if": [
                                                        {"eq": ["teraband_discreto", {"literal": "Cabal"}]},
                                                        1235,
                                                        1234,
                                                    ]},
                                                ]},
                                            ]},
                                        ]},
                                    ]},
                                ]},
                            },
                            {
                                "name": "babala_id",
                                "value": {"case": [
                                    {
                                        "then": {"if": [{"eq": ["tipinho_maroto_id", 2]}, 1234, 12354]},
                                        "when": {"eq": ["teraband_discreto", {"literal": "MasterCard"}]},
                                    },
                                    {"if": [{"eq": ["tipinho_maroto_id", 10]}, 123, 234]},
                                ]},
                            },
                            {
                                "name": "age",
                                "value": {"date": {"if": [
                                    {"eq": ["tipinho_maroto_id", 2]},
                                    {"date_add": [
                                        "dia_da_apresentacaozinha",
                                        {"interval": [
                                            {"add": [28, {"mul": [{"sub": ["installment_number", 1]}, 30]}]},
                                            "day",
                                        ]},
                                    ]},
                                    "dia_da_apresentacaozinha",
                                ]}},
                            },
                            {
                                "name": "hugo_boss",
                                "value": {"sum": {"case": [
                                    {"then": {"pos": "instagram_original"}, "when": {"eq": ["tx_type", 1]}},
                                    {"neg": "instagram_original"},
                                ]}},
                            },
                            {
                                "name": "net_dos_milagres",
                                "value": {"sub": [
                                    {"sum": {"case": [
                                        {"then": {"pos": "instagram_original"}, "when": {"eq": ["tx_type", 1]}},
                                        {"neg": "instagram_original"},
                                    ]}},
                                    {"sum": {"case": [
                                        {"then": {"pos": "amount"}, "when": {"eq": ["tx_type", 1]}},
                                        {"neg": "amount"},
                                    ]}},
                                ]},
                            },
                        ],
                        "where": {"case": [
                            {
                                "then": {"case": [
                                    {
                                        "then": {"eq": [{"date": "dia_da_apresentacaozinha"}, "_reference_date"]},
                                        "when": "is_week_day",
                                    },
                                    {"between": [
                                        {"date": "dia_da_apresentacaozinha"},
                                        {"date_sub": ["_reference_date", {"interval": [1, "day"]}]},
                                        "_reference_date",
                                    ]},
                                ]},
                                "when": {"eq": ["tipinho_maroto_id", 1]},
                            },
                            {"between": [
                                {"date": "dia_da_apresentacaozinha"},
                                {"date_sub": ["_reference_date", {"interval": [1, "day"]}]},
                                "_reference_date",
                            ]},
                        ]},
                    },
                },
            ],
        }
        self.assertEqual(result, expected)

    def test_issue_146(self):
        sql = """SELECT
    sid AS jaguaraquara_id,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_sid') AS task_id,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.channelSid'
    ) AS channel_id,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.conversations.conversation_id'
    ) AS conversation_id,
    JSON_EXTRACT_SCALAR(
          JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
          '$.call_sid'
    ) AS call_id,
    JSON_EXTRACT_SCALAR(
          JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
          '$.conference.sid'
    ) AS call_conference_id,
    JSON_EXTRACT_SCALAR(
          JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
          '$.voiceType'
    ) AS call_type,
    JSON_EXTRACT_SCALAR(
          JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
          '$.from'
    ) AS call_from,
    JSON_EXTRACT_SCALAR(
          JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
          '$.to'
    ) AS call_to,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.conversations.case'
    ) AS forcador_id,
    continha_sid AS twitter_conta_id,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.reservation_sid') AS reservation_id,
    resource_sid AS resource_id,
    resource_type AS event_group,
    event_type,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.fup_project'
    ) AS fup_project,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.ja_vai_nego_velho_id'
    ) AS ja_vai_nego_velho_id,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.fupMessage'
    ) AS fup_message,
    JSON_VALUE_ARRAY(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.hora_de_mofar_ids'
    ) AS hora_de_mofar_ids,
    SAFE_CAST(NULL AS STRING) AS target_changed_reason,
    SAFE_CAST(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_age')
        AS INTEGER
    ) AS task_age,
    SAFE_CAST(NULL AS INTEGER) AS task_age_in_queue,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_assignment_status') AS task_assignment_status,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_channel_unique_name') AS task_channel_name,
    DATETIME(
        SAFE_CAST(
            JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_queue_entered_date')
            AS TIMESTAMP
        ),
        \"America/Sao_Paulo\"
    ) AS task_date_created_at,
    SAFE_CAST(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_priority')
        AS INTEGER
    ) AS task_priority,
    DATETIME(
        SAFE_CAST(
            JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_queue_entered_date')
            AS TIMESTAMP
        ),
        \"America/Sao_Paulo\"
    ) AS task_queue_entered_at,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_queue_name') AS task_queue_name,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_queue_sid') AS task_queue_id,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_queue_target_expression') AS task_queue_target_expression,
    SAFE_CAST(NULL AS STRING) AS task_re_evaluated_reason,
    SAFE_CAST(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_version')
        AS INTEGER
    ) AS task_version,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.task_completed_reason') AS end_reason,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.endReason'
    ) AS end_reason_detailed,
    DATETIME(
        SAFE_CAST(
            JSON_EXTRACT_SCALAR(
                JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
                '$.transferInfo.date'
            ) AS TIMESTAMP
        ),
        \"America/Sao_Paulo\"
    ) AS transfered_at,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.papinhos.papinhos_atributos_1'
    ) AS conversation_attribute_1,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.papinhos.papinhos_atributos_2'
    ) AS conversation_attribute_2,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.papinhos.papinhos_atributos_3'
    ) AS conversation_attribute_3,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.papinhos.papinhos_atributos_4'
    ) AS conversation_attribute_4,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.papinhos.papinhos_atributos_5'
    ) AS conversation_attribute_5,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.papinhos.papinhos_atributos_6'
    ) AS conversation_attribute_6,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.papinhos.papinhos_atributos_7'
    ) AS conversation_attribute_7,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.conversations.initiated_by'
    ) AS initiated_by,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.conversations.canal_de_comunicacao'
    ) AS canal_de_comunicacao,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.channelType'
    ) AS channel_type,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.conversations.phone'
    ) AS customer_phone,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.conversations.email'
    ) AS customer_email,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.conversations.outcome'
    ) AS conversation_outcome,
    SAFE_CAST(
        JSON_EXTRACT_SCALAR(
            JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
            '$.isTransfered'
        ) AS BOOL
    ) AS is_transfered,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.teamOrigin'
    ) AS from_team_transfer,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.ignoreAgent'
    ) AS from_member_transfer,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.transferTargetType'
    ) AS transfer_target_type,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.atributozinhos'),
        '$.annotation'
    ) AS annotation,    
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.trabalho_ativo_nome') AS member_status,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.worker_activity_sid') AS member_activity_id,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.worker_sid') AS member_twilio_id,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.worker_name') AS member_email,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.worker_previous_activity_name') AS member_previous_status,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.worker_previous_activity_sid') AS member_previous_activity_id,
    JSON_EXTRACT_SCALAR(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.worker_attributes'),
        '$.user_role'
    ) AS member_role,
    SAFE_CAST(
        JSON_EXTRACT_SCALAR(balacobaco_data, '$.trabalho_tempo_em_proximos_ativos_sm')
        AS INTEGER
    ) AS member_time_in_previous_activity,
    SAFE_CAST(NULL AS STRING) AS workflow_filter_name,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.workflow_name') AS workflow_name,
    JSON_EXTRACT_SCALAR(balacobaco_data, '$.workflow_sid') AS workflow_id,
    DATETIME(event_date, \"America/Sao_Paulo\") AS created_at
FROM
    `**********.**********.*********` TABLESAMPLE SYSTEM (0.1 PERCENT)
WHERE
    event_date > checkpoint.start_date
    AND event_date <= checkpoint.end_date
QUALIFY ROW_NUMBER() OVER (PARTITION BY sid ORDER BY event_date DESC) = 1
LIMIT 50000"""
        with Timer("parse big sql"):
            result = parse(sql)
        value2json(result)
        expected = {
            "select": [
                {"value": "sid", "name": "jaguaraquara_id"},
                {"value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.task_sid"}]}, "name": "task_id"},
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.channelSid"},
                    ]},
                    "name": "channel_id",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.conversations.conversation_id"},
                    ]},
                    "name": "conversation_id",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.call_sid"},
                    ]},
                    "name": "call_id",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.conference.sid"},
                    ]},
                    "name": "call_conference_id",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.voiceType"},
                    ]},
                    "name": "call_type",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.from"},
                    ]},
                    "name": "call_from",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.to"},
                    ]},
                    "name": "call_to",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.conversations.case"},
                    ]},
                    "name": "forcador_id",
                },
                {"value": "continha_sid", "name": "twitter_conta_id"},
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.reservation_sid"}]},
                    "name": "reservation_id",
                },
                {"value": "resource_sid", "name": "resource_id"},
                {"value": "resource_type", "name": "event_group"},
                {"value": "event_type"},
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.fup_project"},
                    ]},
                    "name": "fup_project",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.ja_vai_nego_velho_id"},
                    ]},
                    "name": "ja_vai_nego_velho_id",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.fupMessage"},
                    ]},
                    "name": "fup_message",
                },
                {
                    "value": {"json_value_array": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.hora_de_mofar_ids"},
                    ]},
                    "name": "hora_de_mofar_ids",
                },
                {"value": {"safe_cast": [{"null": {}}, {"string": {}}]}, "name": "target_changed_reason"},
                {
                    "value": {"safe_cast": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.task_age"}]},
                        {"integer": {}},
                    ]},
                    "name": "task_age",
                },
                {"value": {"safe_cast": [{"null": {}}, {"integer": {}}]}, "name": "task_age_in_queue"},
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.task_assignment_status"}]},
                    "name": "task_assignment_status",
                },
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.task_channel_unique_name"}]},
                    "name": "task_channel_name",
                },
                {
                    "value": {"datetime": [
                        {"safe_cast": [
                            {"json_extract_scalar": ["balacobaco_data", {"literal": "$.task_queue_entered_date"}]},
                            {"timestamp": {}},
                        ]},
                        "America/Sao_Paulo",
                    ]},
                    "name": "task_date_created_at",
                },
                {
                    "value": {"safe_cast": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.task_priority"}]},
                        {"integer": {}},
                    ]},
                    "name": "task_priority",
                },
                {
                    "value": {"datetime": [
                        {"safe_cast": [
                            {"json_extract_scalar": ["balacobaco_data", {"literal": "$.task_queue_entered_date"}]},
                            {"timestamp": {}},
                        ]},
                        "America/Sao_Paulo",
                    ]},
                    "name": "task_queue_entered_at",
                },
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.task_queue_name"}]},
                    "name": "task_queue_name",
                },
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.task_queue_sid"}]},
                    "name": "task_queue_id",
                },
                {
                    "value": {"json_extract_scalar": [
                        "balacobaco_data",
                        {"literal": "$.task_queue_target_expression"},
                    ]},
                    "name": "task_queue_target_expression",
                },
                {"value": {"safe_cast": [{"null": {}}, {"string": {}}]}, "name": "task_re_evaluated_reason"},
                {
                    "value": {"safe_cast": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.task_version"}]},
                        {"integer": {}},
                    ]},
                    "name": "task_version",
                },
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.task_completed_reason"}]},
                    "name": "end_reason",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.endReason"},
                    ]},
                    "name": "end_reason_detailed",
                },
                {
                    "value": {"datetime": [
                        {"safe_cast": [
                            {"json_extract_scalar": [
                                {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                                {"literal": "$.transferInfo.date"},
                            ]},
                            {"timestamp": {}},
                        ]},
                        "America/Sao_Paulo",
                    ]},
                    "name": "transfered_at",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.papinhos.papinhos_atributos_1"},
                    ]},
                    "name": "conversation_attribute_1",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.papinhos.papinhos_atributos_2"},
                    ]},
                    "name": "conversation_attribute_2",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.papinhos.papinhos_atributos_3"},
                    ]},
                    "name": "conversation_attribute_3",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.papinhos.papinhos_atributos_4"},
                    ]},
                    "name": "conversation_attribute_4",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.papinhos.papinhos_atributos_5"},
                    ]},
                    "name": "conversation_attribute_5",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.papinhos.papinhos_atributos_6"},
                    ]},
                    "name": "conversation_attribute_6",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.papinhos.papinhos_atributos_7"},
                    ]},
                    "name": "conversation_attribute_7",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.conversations.initiated_by"},
                    ]},
                    "name": "initiated_by",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.conversations.canal_de_comunicacao"},
                    ]},
                    "name": "canal_de_comunicacao",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.channelType"},
                    ]},
                    "name": "channel_type",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.conversations.phone"},
                    ]},
                    "name": "customer_phone",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.conversations.email"},
                    ]},
                    "name": "customer_email",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.conversations.outcome"},
                    ]},
                    "name": "conversation_outcome",
                },
                {
                    "value": {"safe_cast": [
                        {"json_extract_scalar": [
                            {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                            {"literal": "$.isTransfered"},
                        ]},
                        {"bool": {}},
                    ]},
                    "name": "is_transfered",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.teamOrigin"},
                    ]},
                    "name": "from_team_transfer",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.ignoreAgent"},
                    ]},
                    "name": "from_member_transfer",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.transferTargetType"},
                    ]},
                    "name": "transfer_target_type",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.atributozinhos"}]},
                        {"literal": "$.annotation"},
                    ]},
                    "name": "annotation",
                },
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.trabalho_ativo_nome"}]},
                    "name": "member_status",
                },
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.worker_activity_sid"}]},
                    "name": "member_activity_id",
                },
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.worker_sid"}]},
                    "name": "member_twilio_id",
                },
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.worker_name"}]},
                    "name": "member_email",
                },
                {
                    "value": {"json_extract_scalar": [
                        "balacobaco_data",
                        {"literal": "$.worker_previous_activity_name"},
                    ]},
                    "name": "member_previous_status",
                },
                {
                    "value": {"json_extract_scalar": [
                        "balacobaco_data",
                        {"literal": "$.worker_previous_activity_sid"},
                    ]},
                    "name": "member_previous_activity_id",
                },
                {
                    "value": {"json_extract_scalar": [
                        {"json_extract_scalar": ["balacobaco_data", {"literal": "$.worker_attributes"}]},
                        {"literal": "$.user_role"},
                    ]},
                    "name": "member_role",
                },
                {
                    "value": {"safe_cast": [
                        {"json_extract_scalar": [
                            "balacobaco_data",
                            {"literal": "$.trabalho_tempo_em_proximos_ativos_sm"},
                        ]},
                        {"integer": {}},
                    ]},
                    "name": "member_time_in_previous_activity",
                },
                {"value": {"safe_cast": [{"null": {}}, {"string": {}}]}, "name": "workflow_filter_name"},
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.workflow_name"}]},
                    "name": "workflow_name",
                },
                {
                    "value": {"json_extract_scalar": ["balacobaco_data", {"literal": "$.workflow_sid"}]},
                    "name": "workflow_id",
                },
                {"value": {"datetime": ["event_date", "America/Sao_Paulo"]}, "name": "created_at"},
            ],
            "from": {
                "value": "**********..**********..*********",
                "tablesample": {"method": "system", "percent": 0.1},
            },
            "where": {"and": [
                {"gt": ["event_date", "checkpoint.start_date"]},
                {"lte": ["event_date", "checkpoint.end_date"]},
            ]},
            "qualify": {"eq": [
                {
                    "over": {"partitionby": "sid", "orderby": {"value": "event_date", "sort": "desc"}},
                    "value": {"row_number": {}},
                },
                1,
            ]},
            "limit": 50000,
        }
        self.assertEqual(result, expected)
