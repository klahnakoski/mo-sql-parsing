# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import os
from unittest import TestCase, skip

from mo_files import File
from mo_json import value2json
from mo_logs import logger, strings
from mo_math import randoms
from mo_times import Timer

from mo_sql_parsing import parse, format

IS_TRAVIS = bool(os.environ.get("TRAVIS"))
table = "".maketrans("", "", strings.delchars)


class TestSoQueries(TestCase):
    """
    THESE QUERIES ARE MOSTLY VERY SIMILAR, NOT MANY USEFUL TESTS FOR A PARSER
    """

    @skip("slow")
    def test_so_queries(self):

        def careful_parse(sql):
            if not sql:
                return
            try:
                result = parse(sql)
                new_sql = format(result)
                new_result = parse(new_sql)
                self.assertEqual(result, new_result)
                if randoms.int(50) == 0:
                    logger.info("{{data}}", data=value2json(result))
            except Exception as cause:
                logger.error("failed", cause=cause)

        with Timer("parse so queries") as timer:
            results = (
                File("tests/so_queries/so_queries.tar.zst")
                .content()
                .content()
                .exists()
                .utf8()
                .to_str()
                .map(careful_parse)
                .to_list()
            )
            logger.info(
                "{{num}} results in {{seconds|round(1)}} seconds", num=len(results), seconds=timer.duration.seconds,
            )


def scrub(sql):
    comment = strings.between(sql, "--", "\n")
    while comment:
        sql = sql.replace("--" + comment, "")
        comment = strings.between(sql, "--", "\n")
    return sql.translate(table).lower()
