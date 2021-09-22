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

from moz_sql_parser.sql_parser import SQLParser, scrub_literal, scrub

parseLocker = Lock()  # ENSURE ONLY ONE PARSING AT A TIME


def parse(sql):
    with parseLocker:
        # Handle cases like queries of ('McDonald's | Food Folk ') to {'literal': "McDonald's | Food Folk "}
        sql = sql.rstrip().rstrip(";").replace("'s", "''s")
        parse_result = SQLParser.parseString(sql, parseAll=True)
        return scrub(parse_result)


def format(json, **kwargs):
    from moz_sql_parser.formatting import Formatter
    sql = Formatter(**kwargs).format(json)
    sql = sql.replace('$$null$$', 'null') if isinstance(sql, str) else sql
    return sql


_ = json.dumps

__all__ = ["parse", "format"]
