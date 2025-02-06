# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


from unittest import TestCase

from mo_sql_parsing import parse


class TestApacheHive(TestCase):
    def test_decisive_equailty(self):
        # https://sparkbyexamples.com/apache-hive/hive-relational-arithmetic-logical-operators/#hive-relational-operators
        sql = "select a<=>b from table"
        result = parse(sql)

        self.assertEqual(result, {"select": {"value": {"eq!": ["a", "b"]}}, "from": "table"})
