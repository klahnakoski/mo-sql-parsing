# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#


from unittest import TestCase
from mo_sql_parsing import parse


class TestSqlite(TestCase):
    def test_autoincrement_in_create(self):
        sql = """
        CREATE TABLE Products (
            product_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT
        );
        """
        result = parse(sql)

        self.assertEqual(
            result,
            {
                'create table': {
                    'name': 'Products',
                    'columns': [
                        {'name': 'product_id', 'type': {'integer': {}}, 'primary_key': True, 'autoincrement': True},
                        {'name': 'name', 'type': {'text': {}}, 'nullable': False},
                        {'name': 'price', 'type': {'real': {}}, 'nullable': False},
                        {'name': 'description', 'type': {'text': {}}}
                    ]
                }
            },
        )
