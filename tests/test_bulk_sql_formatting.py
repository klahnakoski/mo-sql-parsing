# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Beto Dealmeida (beto@dealmeida.net)
#


from unittest import skip

from mo_files import File
from mo_logs import logger
from mo_logs.strings import expand_template
from mo_testing.fuzzytestcase import FuzzyTestCase

from mo_sql_parsing import parse, format


test_template = """
    @skip("does not pass yet")
    def test_issue_46_sqlglot_{{num}}(self):
        sql = \"\"\"{{sql}}\"\"\"
        result = parse(sql)
        expected = {}
        self.assertEqual(result, expected)
"""


class TestSimple(FuzzyTestCase):
    @skip("too long")
    def test_files(self):
        count = 0
        acc = []
        for file in File("tests/sql").leaves:
            for i, line in enumerate(file.read_lines()):
                if line.startswith("#"):
                    print(line)
                    continue
                query = line.split("\t")[0]
                query = query.rstrip(";")
                try:
                    parse_result = parse(query)
                    format_result = format(parse_result)
                    logger.note("OK: {{sql}}", sql=format_result)
                except Exception:
                    acc.append(expand_template(test_template, {"sql": query, "num": count}))
                    count += 1

        print("".join(acc))
