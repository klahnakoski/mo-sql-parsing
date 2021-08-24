# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Contact: Kyle Lahnakoski (kyle@lahnakoski.com)
#

from __future__ import absolute_import, division, unicode_literals

import json
from threading import Lock

from mo_sql_parsing.sql_parser import SQLParser, scrub_literal, scrub
import mo_sql_parsing.json_converter import *

parseLocker = Lock()  # ENSURE ONLY ONE PARSING AT A TIME


def parse(sql):
    with parseLocker:
        sql = sql.rstrip().rstrip(";")
        parse_result = SQLParser.parseString(sql, parseAll=True)
        return scrub(parse_result)


def parse_json(sql):
    
    query = sql.lower()
    
    try : 
        query_parsed = {}
        query_reg = parse(query) 
        alias = get_tables(query_reg,{})[1]
        query_parsed['tables_from']  =  get_tables_fj(query_reg, {})[0]
        query_parsed['tables_join']  =  get_tables_fj(query_reg, {})[1]
        query_parsed['projections']  =  get_projections(query_reg, alias)
        query_parsed['attributes_where']   =  get_atts_where(query_reg, alias)
        query_parsed['attributes_groupby'] =  get_atts_group_by(query_reg, alias)
        query_parsed['attributes_orderby'] =  get_atts_order_by(query_reg, alias)
        query_parsed['attributes_having']  =  get_atts_having(query_reg, alias)
        query_parsed['functions']    =  get_functions(query_reg)
        return query_parsed

    except :
        print(query)
        return {}

def format(json, **kwargs):
    from mo_sql_parsing.formatting import Formatter

    return Formatter(**kwargs).format(json)


_ = json.dumps

__all__ = ["parse", "format"]
