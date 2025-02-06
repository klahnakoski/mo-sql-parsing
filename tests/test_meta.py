# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#


import os
import re
import sys
from unittest import TestCase

from mo_future import unichr

from mo_parsing.utils import regex_range
from mo_sql_parsing import sql_parser

_ensure_imported = sql_parser


class TestMeta(TestCase):
    """
    THESE TESTS ARE FOR VERIFYING THE STATE OF THE REPO, NOT THE STATE OF THE CODE
    """

    def test_recursion_limit(self):
        if os.environ.get("TRAVIS_BRANCH") == "master":
            limit = sys.getrecursionlimit()
            self.assertLess(limit, 1500)

    def test_regex_range(self):
        for i in range(9, 4000):
            c = unichr(i)
            pattern = regex_range(c)
            found = re.match(pattern, c)
            self.assertTrue(bool(found))
