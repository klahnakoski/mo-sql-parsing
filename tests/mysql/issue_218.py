expectations = [
    {"set": {"names": "utf8mb4"}},
    {"set": [{"@old_unique_checks": "@@unique_checks"}, {"unique_checks": 0}]},
    {"set": [{"@old_foreign_key_checks": "@@foreign_key_checks"}, {"foreign_key_checks": 0}]},
    {"set": [{"@old_sql_mode": "@@sql_mode"}, {"sql_mode": {"literal": "TRADITIONAL"}}]},
    {"drop": {"schema": "sakila", "if_exists": True}},
    {"create_schema": {"name": "sakila"}},
    {"use": "sakila"},
    {"create table": {
        "columns": [
            {
                "auto_increment": True,
                "name": "actor_id",
                "nullable": False,
                "type": {"smallint": {}, "unsigned": True},
            },
            {"name": "first_name", "nullable": False, "type": {"varchar": 45}},
            {"name": "last_name", "nullable": False, "type": {"varchar": 45}},
            {
                "default": "CURRENT_TIMESTAMP",
                "name": "last_update",
                "nullable": False,
                "on_update": "CURRENT_TIMESTAMP",
                "type": {"timestamp": {}},
            },
        ],
        "constraint": [
            {"primary_key": {"columns": "actor_id"}},
            {"index": {"columns": "last_name", "name": "idx_actor_last_name"}},
        ],
        "default_charset": "utf8mb4",
        "engine": "InnoDB",
        "name": "actor",
        "replace": False,
    }},
    {"create table": {
        "columns": [
            {
                "auto_increment": True,
                "name": "address_id",
                "nullable": False,
                "type": {"smallint": {}, "unsigned": True},
            },
            {"name": "address", "nullable": False, "type": {"varchar": 50}},
            {"default": {"null": {}}, "name": "address2", "type": {"varchar": 50}},
            {"name": "district", "nullable": False, "type": {"varchar": 20}},
            {"name": "city_id", "nullable": False, "type": {"smallint": {}, "unsigned": True}},
            {"default": {"null": {}}, "name": "postal_code", "type": {"varchar": 10}},
            {"name": "phone", "nullable": False, "type": {"varchar": 20}},
            {
                "default": "CURRENT_TIMESTAMP",
                "name": "last_update",
                "nullable": False,
                "on_update": "CURRENT_TIMESTAMP",
                "type": {"timestamp": {}},
            },
        ],
        "constraint": [
            {"primary_key": {"columns": "address_id"}},
            {"index": {"columns": "city_id", "name": "idx_fk_city_id"}},
            {
                "foreign_key": {
                    "columns": "city_id",
                    "on_delete": "restrict",
                    "on_update": "cascade",
                    "references": {"columns": "city_id", "table": "city"},
                },
                "name": "fk_address_city",
            },
        ],
        "default_charset": "utf8mb4",
        "engine": "InnoDB",
        "name": "address",
    }},
    {"create table": {
        "columns": [
            {
                "auto_increment": True,
                "name": "category_id",
                "nullable": False,
                "type": {"tinyint": {}, "unsigned": True},
            },
            {"name": "name", "nullable": False, "type": {"varchar": 25}},
            {
                "default": "CURRENT_TIMESTAMP",
                "name": "last_update",
                "nullable": False,
                "on_update": "CURRENT_TIMESTAMP",
                "type": {"timestamp": {}},
            },
        ],
        "constraint": {"primary_key": {"columns": "category_id"}},
        "default_charset": "utf8mb4",
        "engine": "InnoDB",
        "name": "category",
    }},
    {"create table": {
        "columns": [
            {
                "auto_increment": True,
                "name": "city_id",
                "nullable": False,
                "type": {"smallint": {}, "unsigned": True},
            },
            {"name": "city", "nullable": False, "type": {"varchar": 50}},
            {"name": "country_id", "nullable": False, "type": {"smallint": {}, "unsigned": True}},
            {
                "default": "CURRENT_TIMESTAMP",
                "name": "last_update",
                "nullable": False,
                "on_update": "CURRENT_TIMESTAMP",
                "type": {"timestamp": {}},
            },
        ],
        "constraint": [
            {"primary_key": {"columns": "city_id"}},
            {"index": {"columns": "country_id", "name": "idx_fk_country_id"}},
            {
                "foreign_key": {
                    "columns": "country_id",
                    "on_delete": "restrict",
                    "on_update": "cascade",
                    "references": {"columns": "country_id", "table": "country"},
                },
                "name": "fk_city_country",
            },
        ],
        "default_charset": "utf8mb4",
        "engine": "InnoDB",
        "name": "city",
    }},
    {"create table": {
        "columns": [
            {
                "auto_increment": True,
                "name": "country_id",
                "nullable": False,
                "type": {"smallint": {}, "unsigned": True},
            },
            {"name": "country", "nullable": False, "type": {"varchar": 50}},
            {
                "default": "CURRENT_TIMESTAMP",
                "name": "last_update",
                "nullable": False,
                "on_update": "CURRENT_TIMESTAMP",
                "type": {"timestamp": {}},
            },
        ],
        "constraint": {"primary_key": {"columns": "country_id"}},
        "default_charset": "utf8mb4",
        "engine": "InnoDB",
        "name": "country",
    }},
    {"create table": {
        "columns": [
            {
                "auto_increment": True,
                "name": "customer_id",
                "nullable": False,
                "type": {"smallint": {}, "unsigned": True},
            },
            {"name": "store_id", "nullable": False, "type": {"tinyint": {}, "unsigned": True}},
            {"name": "first_name", "nullable": False, "type": {"varchar": 45}},
            {"name": "last_name", "nullable": False, "type": {"varchar": 45}},
            {"default": {"null": {}}, "name": "email", "type": {"varchar": 50}},
            {"name": "address_id", "nullable": False, "type": {"smallint": {}, "unsigned": True}},
            {"default": True, "name": "active", "nullable": False, "type": {"boolean": {}}},
            {"name": "create_date", "nullable": False, "type": {"datetime": {}}},
            {
                "default": "CURRENT_TIMESTAMP",
                "name": "last_update",
                "on_update": "CURRENT_TIMESTAMP",
                "type": {"timestamp": {}},
            },
        ],
        "constraint": [
            {"primary_key": {"columns": "customer_id"}},
            {"index": {"columns": "store_id", "name": "idx_fk_store_id"}},
            {"index": {"columns": "address_id", "name": "idx_fk_address_id"}},
            {"index": {"columns": "last_name", "name": "idx_last_name"}},
            {
                "foreign_key": {
                    "columns": "address_id",
                    "on_delete": "restrict",
                    "on_update": "cascade",
                    "references": {"columns": "address_id", "table": "address"},
                },
                "name": "fk_customer_address",
            },
            {
                "foreign_key": {
                    "columns": "store_id",
                    "on_delete": "restrict",
                    "on_update": "cascade",
                    "references": {"columns": "store_id", "table": "store"},
                },
                "name": "fk_customer_store",
            },
        ],
        "default_charset": "utf8mb4",
        "engine": "InnoDB",
        "name": "customer",
    }},
    {"create table": {
        "columns": [
            {
                "auto_increment": True,
                "name": "film_id",
                "nullable": False,
                "type": {"smallint": {}, "unsigned": True},
            },
            {"name": "title", "nullable": False, "type": {"varchar": 128}},
            {"default": {"null": {}}, "name": "description", "type": {"text": {}}},
            {"default": {"null": {}}, "name": "release_year", "type": "YEAR"},
            {"name": "language_id", "nullable": False, "type": {"tinyint": {}, "unsigned": True}},
            {"default": {"null": {}}, "name": "original_language_id", "type": {"tinyint": {}, "unsigned": True}},
            {"default": 3, "name": "rental_duration", "nullable": False, "type": {"tinyint": {}, "unsigned": True},},
            {"default": 4.99, "name": "rental_rate", "nullable": False, "type": {"decimal": [4, 2]}},
            {"default": {"null": {}}, "name": "length", "type": {"smallint": {}, "unsigned": True}},
            {"default": 19.99, "name": "replacement_cost", "nullable": False, "type": {"decimal": [5, 2]}},
            {
                "default": {"literal": "G"},
                "name": "rating",
                "type": {"enum": [
                    {"literal": "G"},
                    {"literal": "PG"},
                    {"literal": "PG-13"},
                    {"literal": "R"},
                    {"literal": "NC-17"},
                ]},
            },
            {
                "default": {"null": {}},
                "name": "special_features",
                "type": {"set": [
                    {"literal": "Trailers"},
                    {"literal": "Commentaries"},
                    {"literal": "Deleted Scenes"},
                    {"literal": "Behind the Scenes"},
                ]},
            },
            {
                "default": "CURRENT_TIMESTAMP",
                "name": "last_update",
                "nullable": False,
                "on_update": "CURRENT_TIMESTAMP",
                "type": {"timestamp": {}},
            },
        ],
        "constraint": [
            {"primary_key": {"columns": "film_id"}},
            {"index": {"columns": "title", "name": "idx_title"}},
            {"index": {"columns": "language_id", "name": "idx_fk_language_id"}},
            {"index": {"columns": "original_language_id", "name": "idx_fk_original_language_id"}},
            {
                "foreign_key": {
                    "columns": "language_id",
                    "on_delete": "restrict",
                    "on_update": "cascade",
                    "references": {"columns": "language_id", "table": "language"},
                },
                "name": "fk_film_language",
            },
            {
                "foreign_key": {
                    "columns": "original_language_id",
                    "on_delete": "restrict",
                    "on_update": "cascade",
                    "references": {"columns": "language_id", "table": "language"},
                },
                "name": "fk_film_language_original",
            },
        ],
        "default_charset": "utf8mb4",
        "engine": "InnoDB",
        "name": "film",
    }},
    {"create table": {
        "columns": [
            {"name": "actor_id", "nullable": False, "type": {"smallint": {}, "unsigned": True}},
            {"name": "film_id", "nullable": False, "type": {"smallint": {}, "unsigned": True}},
            {
                "default": "CURRENT_TIMESTAMP",
                "name": "last_update",
                "nullable": False,
                "on_update": "CURRENT_TIMESTAMP",
                "type": {"timestamp": {}},
            },
        ],
        "constraint": [
            {"primary_key": {"columns": ["actor_id", "film_id"]}},
            {"index": {"columns": "film_id", "name": "idx_fk_film_id"}},
            {
                "foreign_key": {
                    "columns": "actor_id",
                    "on_delete": "restrict",
                    "on_update": "cascade",
                    "references": {"columns": "actor_id", "table": "actor"},
                },
                "name": "fk_film_actor_actor",
            },
            {
                "foreign_key": {
                    "columns": "film_id",
                    "on_delete": "restrict",
                    "on_update": "cascade",
                    "references": {"columns": "film_id", "table": "film"},
                },
                "name": "fk_film_actor_film",
            },
        ],
        "default_charset": "utf8mb4",
        "engine": "InnoDB",
        "name": "film_actor",
    }},
    {"create table": {
        "columns": [
            {"name": "film_id", "nullable": False, "type": {"smallint": {}, "unsigned": True}},
            {"name": "category_id", "nullable": False, "type": {"tinyint": {}, "unsigned": True}},
            {
                "default": "CURRENT_TIMESTAMP",
                "name": "last_update",
                "nullable": False,
                "on_update": "CURRENT_TIMESTAMP",
                "type": {"timestamp": {}},
            },
        ],
        "constraint": [
            {"primary_key": {"columns": ["film_id", "category_id"]}},
            {
                "foreign_key": {
                    "columns": "film_id",
                    "on_delete": "restrict",
                    "on_update": "cascade",
                    "references": {"columns": "film_id", "table": "film"},
                },
                "name": "fk_film_category_film",
            },
            {
                "foreign_key": {
                    "columns": "category_id",
                    "on_delete": "restrict",
                    "on_update": "cascade",
                    "references": {"columns": "category_id", "table": "category"},
                },
                "name": "fk_film_category_category",
            },
        ],
        "default_charset": "utf8mb4",
        "engine": "InnoDB",
        "name": "film_category",
    }},
    {"set": {"@old_default_storage_engine": "@@default_storage_engine"}},
    {"set": {"@@default_storage_engine": {"literal": "MyISAM"}}},
    None,
    {"create table": {
        "columns": [
            {"name": "film_id", "nullable": False, "type": {"smallint": {}, "unsigned": True}},
            {"name": "title", "nullable": False, "type": {"varchar": 255}},
            {"name": "description", "type": {"text": {}}},
        ],
        "constraint": [
            {"primary_key": {"columns": "film_id"}},
            {"fulltext_key": {"columns": ["title", "description"], "name": "idx_title_description"}},
        ],
        "default_charset": "utf8mb4",
        "name": "film_text",
    }},
    {"set": {"@@default_storage_engine": "@old_default_storage_engine"}},
    None,
    {"delimiter": ";;"},
    {"create_trigger": {
        "name": "ins_film",
        "when": "after",
        "event": "insert",
        "table": "film",
        "body": {"block": {
            "columns": ["film_id", "title", "description"],
            "query": {"select": [{"value": "new.film_id"}, {"value": "new.title"}, {"value": "new.description"}]},
            "insert": "film_text",
        }},
    }},
    {"create_trigger": {
        "name": "upd_film",
        "when": "after",
        "event": "update",
        "table": "film",
        "body": {"block": {
            "if": {"or": [
                {"neq": ["old.title", "new.title"]},
                {"neq": ["old.description", "new.description"]},
                {"neq": ["old.film_id", "new.film_id"]},
            ]},
            "then": {
                "set": {"title": "new.title", "description": "new.description", "film_id": "new.film_id"},
                "where": {"eq": ["film_id", "old.film_id"]},
                "update": "film_text",
            },
        }},
    }},
    {"create_trigger": {
        "name": "del_film",
        "when": "after",
        "event": "delete",
        "table": "film",
        "body": {"block": {"where": {"eq": ["film_id", "old.film_id"]}, "delete": "film_text"}},
    }},
    None,
    {"delimiter": ";"},
    {"create table": {
        "name": "inventory",
        "columns": [
            {
                "name": "inventory_id",
                "type": {"unsigned": True, "mediumint": {}},
                "nullable": False,
                "auto_increment": True,
            },
            {"name": "film_id", "type": {"unsigned": True, "smallint": {}}, "nullable": False},
            {"name": "store_id", "type": {"unsigned": True, "tinyint": {}}, "nullable": False},
            {
                "name": "last_update",
                "type": {"timestamp": {}},
                "nullable": False,
                "default": "CURRENT_TIMESTAMP",
                "on_update": "CURRENT_TIMESTAMP",
            },
        ],
        "constraint": [
            {"primary_key": {"columns": "inventory_id"}},
            {"index": {"name": "idx_fk_film_id", "columns": "film_id"}},
            {"index": {"name": "idx_store_id_film_id", "columns": ["store_id", "film_id"]}},
            {
                "name": "fk_inventory_store",
                "foreign_key": {
                    "columns": "store_id",
                    "references": {"table": "store", "columns": "store_id"},
                    "on_delete": "restrict",
                    "on_update": "cascade",
                },
            },
            {
                "name": "fk_inventory_film",
                "foreign_key": {
                    "columns": "film_id",
                    "references": {"table": "film", "columns": "film_id"},
                    "on_delete": "restrict",
                    "on_update": "cascade",
                },
            },
        ],
        "engine": "InnoDB",
        "default_charset": "utf8mb4",
    }},
    {"create table": {
        "name": "language",
        "columns": [
            {
                "name": "language_id",
                "type": {"unsigned": True, "tinyint": {}},
                "nullable": False,
                "auto_increment": True,
            },
            {"name": "name", "type": {"char": 20}, "nullable": False},
            {
                "name": "last_update",
                "type": {"timestamp": {}},
                "nullable": False,
                "default": "CURRENT_TIMESTAMP",
                "on_update": "CURRENT_TIMESTAMP",
            },
        ],
        "constraint": {"primary_key": {"columns": "language_id"}},
        "engine": "InnoDB",
        "default_charset": "utf8mb4",
    }},
    {"create table": {
        "name": "payment",
        "columns": [
            {
                "name": "payment_id",
                "type": {"unsigned": True, "smallint": {}},
                "nullable": False,
                "auto_increment": True,
            },
            {"name": "customer_id", "type": {"unsigned": True, "smallint": {}}, "nullable": False},
            {"name": "staff_id", "type": {"unsigned": True, "tinyint": {}}, "nullable": False},
            {"name": "rental_id", "type": {"int": {}}, "default": {"null": {}}},
            {"name": "amount", "type": {"decimal": [5, 2]}, "nullable": False},
            {"name": "payment_date", "type": {"datetime": {}}, "nullable": False},
            {
                "name": "last_update",
                "type": {"timestamp": {}},
                "default": "CURRENT_TIMESTAMP",
                "on_update": "CURRENT_TIMESTAMP",
            },
        ],
        "constraint": [
            {"primary_key": {"columns": "payment_id"}},
            {"index": {"name": "idx_fk_staff_id", "columns": "staff_id"}},
            {"index": {"name": "idx_fk_customer_id", "columns": "customer_id"}},
            {
                "name": "fk_payment_rental",
                "foreign_key": {
                    "columns": "rental_id",
                    "references": {"table": "rental", "columns": "rental_id"},
                    "on_delete": "set_null",
                    "on_update": "cascade",
                },
            },
            {
                "name": "fk_payment_customer",
                "foreign_key": {
                    "columns": "customer_id",
                    "references": {"table": "customer", "columns": "customer_id"},
                    "on_delete": "restrict",
                    "on_update": "cascade",
                },
            },
            {
                "name": "fk_payment_staff",
                "foreign_key": {
                    "columns": "staff_id",
                    "references": {"table": "staff", "columns": "staff_id"},
                    "on_delete": "restrict",
                    "on_update": "cascade",
                },
            },
        ],
        "engine": "InnoDB",
        "default_charset": "utf8mb4",
    }},
    {"create table": {
        "name": "rental",
        "columns": [
            {"name": "rental_id", "type": {"int": {}}, "nullable": False, "auto_increment": True},
            {"name": "rental_date", "type": {"datetime": {}}, "nullable": False},
            {"name": "inventory_id", "type": {"unsigned": True, "mediumint": {}}, "nullable": False},
            {"name": "customer_id", "type": {"unsigned": True, "smallint": {}}, "nullable": False},
            {"name": "return_date", "type": {"datetime": {}}, "default": {"null": {}}},
            {"name": "staff_id", "type": {"unsigned": True, "tinyint": {}}, "nullable": False},
            {
                "name": "last_update",
                "type": {"timestamp": {}},
                "nullable": False,
                "default": "CURRENT_TIMESTAMP",
                "on_update": "CURRENT_TIMESTAMP",
            },
        ],
        "constraint": [
            {"primary_key": {"columns": "rental_id"}},
            {"index": {"unique": True, "columns": ["rental_date", "inventory_id", "customer_id"]}},
            {"index": {"name": "idx_fk_inventory_id", "columns": "inventory_id"}},
            {"index": {"name": "idx_fk_customer_id", "columns": "customer_id"}},
            {"index": {"name": "idx_fk_staff_id", "columns": "staff_id"}},
            {
                "name": "fk_rental_staff",
                "foreign_key": {
                    "columns": "staff_id",
                    "references": {"table": "staff", "columns": "staff_id"},
                    "on_delete": "restrict",
                    "on_update": "cascade",
                },
            },
            {
                "name": "fk_rental_inventory",
                "foreign_key": {
                    "columns": "inventory_id",
                    "references": {"table": "inventory", "columns": "inventory_id"},
                    "on_delete": "restrict",
                    "on_update": "cascade",
                },
            },
            {
                "name": "fk_rental_customer",
                "foreign_key": {
                    "columns": "customer_id",
                    "references": {"table": "customer", "columns": "customer_id"},
                    "on_delete": "restrict",
                    "on_update": "cascade",
                },
            },
        ],
        "engine": "InnoDB",
        "default_charset": "utf8mb4",
    }},
    {"create table": {
        "name": "staff",
        "columns": [
            {"name": "staff_id", "type": {"unsigned": True, "tinyint": {}}, "nullable": False, "auto_increment": True},
            {"name": "first_name", "type": {"varchar": 45}, "nullable": False},
            {"name": "last_name", "type": {"varchar": 45}, "nullable": False},
            {"name": "address_id", "type": {"unsigned": True, "smallint": {}}, "nullable": False},
            {"name": "picture", "type": {"blob": {}}, "default": {"null": {}}},
            {"name": "email", "type": {"varchar": 50}, "default": {"null": {}}},
            {"name": "store_id", "type": {"unsigned": True, "tinyint": {}}, "nullable": False},
            {"name": "active", "type": {"boolean": {}}, "nullable": False, "default": True},
            {"name": "username", "type": {"varchar": 16}, "nullable": False},
            {
                "name": "password",
                "type": {"varchar": 40},
                "collate": "utf8mb4_bin",
                "default": {"null": {}},
                "character_set": "utf8mb4",
            },
            {
                "name": "last_update",
                "type": {"timestamp": {}},
                "nullable": False,
                "default": "CURRENT_TIMESTAMP",
                "on_update": "CURRENT_TIMESTAMP",
            },
        ],
        "constraint": [
            {"primary_key": {"columns": "staff_id"}},
            {"index": {"name": "idx_fk_store_id", "columns": "store_id"}},
            {"index": {"name": "idx_fk_address_id", "columns": "address_id"}},
            {
                "name": "fk_staff_store",
                "foreign_key": {
                    "columns": "store_id",
                    "references": {"table": "store", "columns": "store_id"},
                    "on_delete": "restrict",
                    "on_update": "cascade",
                },
            },
            {
                "name": "fk_staff_address",
                "foreign_key": {
                    "columns": "address_id",
                    "references": {"table": "address", "columns": "address_id"},
                    "on_delete": "restrict",
                    "on_update": "cascade",
                },
            },
        ],
        "engine": "InnoDB",
        "default_charset": "utf8mb4",
    }},
    {"create table": {
        "name": "store",
        "columns": [
            {"name": "store_id", "type": {"unsigned": True, "tinyint": {}}, "nullable": False, "auto_increment": True},
            {"name": "manager_staff_id", "type": {"unsigned": True, "tinyint": {}}, "nullable": False},
            {"name": "address_id", "type": {"unsigned": True, "smallint": {}}, "nullable": False},
            {
                "name": "last_update",
                "type": {"timestamp": {}},
                "nullable": False,
                "default": "CURRENT_TIMESTAMP",
                "on_update": "CURRENT_TIMESTAMP",
            },
        ],
        "constraint": [
            {"primary_key": {"columns": "store_id"}},
            {"index": {"unique": True, "name": "idx_unique_manager", "columns": "manager_staff_id"}},
            {"index": {"name": "idx_fk_address_id", "columns": "address_id"}},
            {
                "name": "fk_store_staff",
                "foreign_key": {
                    "columns": "manager_staff_id",
                    "references": {"table": "staff", "columns": "staff_id"},
                    "on_delete": "restrict",
                    "on_update": "cascade",
                },
            },
            {
                "name": "fk_store_address",
                "foreign_key": {
                    "columns": "address_id",
                    "references": {"table": "address", "columns": "address_id"},
                    "on_delete": "restrict",
                    "on_update": "cascade",
                },
            },
        ],
        "engine": "InnoDB",
        "default_charset": "utf8mb4",
    }},
    {"create view": {
        "name": "customer_list",
        "query": {
            "select": [
                {"name": "ID", "value": "cu.customer_id"},
                {
                    "name": "name",
                    "value": {"concat": ["cu.first_name", {"literal": " ", "encoding": "_utf8mb4"}, "cu.last_name"]},
                },
                {"name": "address", "value": "a.address"},
                {"name": "zip code", "value": "a.postal_code"},
                {"name": "phone", "value": "a.phone"},
                {"name": "city", "value": "city.city"},
                {"name": "country", "value": "country.country"},
                {
                    "name": "notes",
                    "value": {"if": [
                        "cu.active",
                        {"literal": "active", "encoding": "_utf8mb4"},
                        {"literal": "", "encoding": "_utf8mb4"},
                    ]},
                },
                {"name": "SID", "value": "cu.store_id"},
            ],
            "from": [
                {"value": "customer", "name": "cu"},
                {"join": {"value": "address", "name": "a"}, "on": {"eq": ["cu.address_id", "a.address_id"]}},
                {"join": "city", "on": {"eq": ["a.city_id", "city.city_id"]}},
                {"join": "country", "on": {"eq": ["city.country_id", "country.country_id"]}},
            ],
        },
    }},
    {"create view": {
        "name": "film_list",
        "query": {
            "select": [
                {"name": "FID", "value": "film.film_id"},
                {"name": "title", "value": "film.title"},
                {"name": "description", "value": "film.description"},
                {"name": "category", "value": "category.name"},
                {"name": "price", "value": "film.rental_rate"},
                {"name": "length", "value": "film.length"},
                {"name": "rating", "value": "film.rating"},
                {
                    "name": "actors",
                    "value": {
                        "separator": {"literal": ", "},
                        "group_concat": {"concat": [
                            "actor.first_name",
                            {"literal": " ", "encoding": "_utf8mb4"},
                            "actor.last_name",
                        ]},
                    },
                },
            ],
            "from": [
                "film",
                {"left join": "film_category", "on": {"eq": ["film_category.film_id", "film.film_id"]}},
                {"left join": "category", "on": {"eq": ["category.category_id", "film_category.category_id"]}},
                {"left join": "film_actor", "on": {"eq": ["film.film_id", "film_actor.film_id"]}},
                {"left join": "actor", "on": {"eq": ["film_actor.actor_id", "actor.actor_id"]}},
            ],
            "groupby": [{"value": "film.film_id"}, {"value": "category.name"}],
        },
    }},
    {"create view": {
        "name": "nicer_but_slower_film_list",
        "query": {
            "select": [
                {"name": "FID", "value": "film.film_id"},
                {"name": "title", "value": "film.title"},
                {"name": "description", "value": "film.description"},
                {"name": "category", "value": "category.name"},
                {"name": "price", "value": "film.rental_rate"},
                {"name": "length", "value": "film.length"},
                {"name": "rating", "value": "film.rating"},
                {
                    "name": "actors",
                    "value": {
                        "separator": {"literal": ", "},
                        "group_concat": {"concat": {"concat": [
                            {"ucase": {"substr": ["actor.first_name", 1, 1]}},
                            {"lcase": {"substr": ["actor.first_name", 2, {"length": "actor.first_name"}]}},
                            {"literal": " ", "encoding": "_utf8mb4"},
                            {"concat": [
                                {"ucase": {"substr": ["actor.last_name", 1, 1]}},
                                {"lcase": {"substr": ["actor.last_name", 2, {"length": "actor.last_name"}]}},
                            ]},
                        ]}},
                    },
                },
            ],
            "from": [
                "film",
                {"left join": "film_category", "on": {"eq": ["film_category.film_id", "film.film_id"]}},
                {"left join": "category", "on": {"eq": ["category.category_id", "film_category.category_id"]}},
                {"left join": "film_actor", "on": {"eq": ["film.film_id", "film_actor.film_id"]}},
                {"left join": "actor", "on": {"eq": ["film_actor.actor_id", "actor.actor_id"]}},
            ],
            "groupby": [{"value": "film.film_id"}, {"value": "category.name"}],
        },
    }},
    {"create view": {
        "name": "staff_list",
        "query": {
            "select": [
                {"name": "ID", "value": "s.staff_id"},
                {
                    "name": "name",
                    "value": {"concat": ["s.first_name", {"literal": " ", "encoding": "_utf8mb4"}, "s.last_name"]},
                },
                {"name": "address", "value": "a.address"},
                {"name": "zip code", "value": "a.postal_code"},
                {"name": "phone", "value": "a.phone"},
                {"name": "city", "value": "city.city"},
                {"name": "country", "value": "country.country"},
                {"name": "SID", "value": "s.store_id"},
            ],
            "from": [
                {"value": "staff", "name": "s"},
                {"join": {"value": "address", "name": "a"}, "on": {"eq": ["s.address_id", "a.address_id"]}},
                {"join": "city", "on": {"eq": ["a.city_id", "city.city_id"]}},
                {"join": "country", "on": {"eq": ["city.country_id", "country.country_id"]}},
            ],
        },
    }},
    {"create view": {
        "name": "sales_by_store",
        "query": {
            "select": [
                {
                    "name": "store",
                    "value": {"concat": ["c.city", {"literal": ",", "encoding": "_utf8mb4"}, "cy.country"]},
                },
                {
                    "name": "manager",
                    "value": {"concat": ["m.first_name", {"literal": " ", "encoding": "_utf8mb4"}, "m.last_name"]},
                },
                {"name": "total_sales", "value": {"sum": "p.amount"}},
            ],
            "from": [
                {"value": "payment", "name": "p"},
                {"inner join": {"value": "rental", "name": "r"}, "on": {"eq": ["p.rental_id", "r.rental_id"]}},
                {
                    "inner join": {"value": "inventory", "name": "i"},
                    "on": {"eq": ["r.inventory_id", "i.inventory_id"]},
                },
                {"inner join": {"value": "store", "name": "s"}, "on": {"eq": ["i.store_id", "s.store_id"]}},
                {"inner join": {"value": "address", "name": "a"}, "on": {"eq": ["s.address_id", "a.address_id"]}},
                {"inner join": {"value": "city", "name": "c"}, "on": {"eq": ["a.city_id", "c.city_id"]}},
                {"inner join": {"value": "country", "name": "cy"}, "on": {"eq": ["c.country_id", "cy.country_id"]}},
                {"inner join": {"value": "staff", "name": "m"}, "on": {"eq": ["s.manager_staff_id", "m.staff_id"]}},
            ],
            "groupby": {"value": "s.store_id"},
            "orderby": [{"value": "cy.country"}, {"value": "c.city"}],
        },
    }},
    {"create view": {
        "name": "sales_by_film_category",
        "query": {
            "select": [{"name": "category", "value": "c.name"}, {"name": "total_sales", "value": {"sum": "p.amount"}}],
            "from": [
                {"value": "payment", "name": "p"},
                {"inner join": {"value": "rental", "name": "r"}, "on": {"eq": ["p.rental_id", "r.rental_id"]}},
                {
                    "inner join": {"value": "inventory", "name": "i"},
                    "on": {"eq": ["r.inventory_id", "i.inventory_id"]},
                },
                {"inner join": {"value": "film", "name": "f"}, "on": {"eq": ["i.film_id", "f.film_id"]}},
                {"inner join": {"value": "film_category", "name": "fc"}, "on": {"eq": ["f.film_id", "fc.film_id"]}},
                {"inner join": {"value": "category", "name": "c"}, "on": {"eq": ["fc.category_id", "c.category_id"]}},
            ],
            "groupby": {"value": "c.name"},
            "orderby": {"value": "total_sales", "sort": "desc"},
        },
    }},
    {"create view": {
        "definer": "CURRENT_USER",
        "sql_security": "invoker",
        "name": "actor_info",
        "query": {
            "select": [
                {"value": "a.actor_id"},
                {"value": "a.first_name"},
                {"value": "a.last_name"},
                {
                    "name": "film_info",
                    "value": {
                        "distinct": True,
                        "orderby": {"value": "c.name"},
                        "separator": {"literal": "; "},
                        "group_concat": {"concat": [
                            "c.name",
                            {"literal": ": "},
                            {
                                "select": {"value": {
                                    "orderby": {"value": "f.title"},
                                    "separator": {"literal": ", "},
                                    "group_concat": "f.title",
                                }},
                                "from": [
                                    {"value": "sakila.film", "name": "f"},
                                    {
                                        "inner join": {"value": "sakila.film_category", "name": "fc"},
                                        "on": {"eq": ["f.film_id", "fc.film_id"]},
                                    },
                                    {
                                        "inner join": {"value": "sakila.film_actor", "name": "fa"},
                                        "on": {"eq": ["f.film_id", "fa.film_id"]},
                                    },
                                ],
                                "where": {"and": [
                                    {"eq": ["fc.category_id", "c.category_id"]},
                                    {"eq": ["fa.actor_id", "a.actor_id"]},
                                ]},
                            },
                        ]},
                    },
                },
            ],
            "from": [
                {"value": "sakila.actor", "name": "a"},
                {
                    "left join": {"value": "sakila.film_actor", "name": "fa"},
                    "on": {"eq": ["a.actor_id", "fa.actor_id"]},
                },
                {
                    "left join": {"value": "sakila.film_category", "name": "fc"},
                    "on": {"eq": ["fa.film_id", "fc.film_id"]},
                },
                {
                    "left join": {"value": "sakila.category", "name": "c"},
                    "on": {"eq": ["fc.category_id", "c.category_id"]},
                },
            ],
            "groupby": [{"value": "a.actor_id"}, {"value": "a.first_name"}, {"value": "a.last_name"}],
        },
    }},
    None,
    {"delimiter": "//"},
    {"create_procedure": {
        "name": "rewards_report",
        "params": [
            {"mode": "in", "name": "min_monthly_purchases", "type": {"unsigned": True, "tinyint": {}}},
            {"mode": "in", "name": "min_dollar_amount_purchased", "type": {"decimal": [10, 2]}},
            {"mode": "out", "name": "count_rewardees", "type": {"int": {}}},
        ],
        "language": "sql",
        "sql_security": "definer",
        "comment": {"literal": "Provides a customizable report on best customers"},
        "body": {
            "label": "proc",
            "block": [
                {"declare": {"name": "last_month_start", "type": {"date": {}}}},
                {"declare": {"name": "last_month_end", "type": {"date": {}}}},
                {
                    "if": {"eq": ["min_monthly_purchases", 0]},
                    "then": [
                        {"select": {"value": {"literal": "Minimum monthly purchases parameter must be > 0"}}},
                        {"leave": "proc"},
                    ],
                },
                {
                    "if": {"eq": ["min_dollar_amount_purchased", 0.0]},
                    "then": [
                        {"select": {"value": {
                            "literal": "Minimum monthly dollar amount purchased parameter must be > $0.00"
                        }}},
                        {"leave": "proc"},
                    ],
                },
                {"set": {"last_month_start": {"date_sub": [{"current_date": {}}, {"interval": [1, "month"]}]}}},
                {"set": {"last_month_start": {"str_to_date": [
                    {"concat": [
                        {"year": "last_month_start"},
                        {"literal": "-"},
                        {"month": "last_month_start"},
                        {"literal": "-01"},
                    ]},
                    {"literal": "%Y-%m-%d"},
                ]}}},
                {"set": {"last_month_end": {"last_day": "last_month_start"}}},
                {"create table": {
                    "temporary": True,
                    "name": "tmpCustomer",
                    "columns": {
                        "name": "customer_id",
                        "type": {"unsigned": True, "smallint": {}},
                        "nullable": False,
                        "primary_key": True,
                    },
                }},
                {
                    "columns": "customer_id",
                    "query": {
                        "select": {"value": "p.customer_id"},
                        "from": {"value": "payment", "name": "p"},
                        "where": {"between": [{"date": "p.payment_date"}, "last_month_start", "last_month_end"]},
                        "groupby": {"value": "customer_id"},
                        "having": {"and": [
                            {"gt": [{"sum": "p.amount"}, "min_dollar_amount_purchased"]},
                            {"gt": [{"count": "customer_id"}, "min_monthly_purchases"]},
                        ]},
                    },
                    "insert": "tmpCustomer",
                },
                {"select": {"value": {"count": "*"}}, "from": "tmpCustomer", "into": "count_rewardees"},
                {
                    "select": {"value": "c.*"},
                    "from": [
                        {"value": "tmpCustomer", "name": "t"},
                        {
                            "inner join": {"value": "customer", "name": "c"},
                            "on": {"eq": ["t.customer_id", "c.customer_id"]},
                        },
                    ],
                },
                {"drop": {"table": "tmpCustomer"}},
            ],
        },
    }},
    None,
    {"delimiter": ";"},
    {"delimiter": "$$"},
    {"create_function": {
        "name": "get_customer_balance",
        "params": [
            {"name": "p_customer_id", "type": {"int": {}}},
            {"name": "p_effective_date", "type": {"datetime": {}}},
        ],
        "returns": {"decimal": [5, 2]},
        "body": {"block": [
            {"declare": {"name": "v_rentfees", "type": {"decimal": [5, 2]}}},
            {"declare": {"name": "v_overfees", "type": {"integer": {}}}},
            {"declare": {"name": "v_payments", "type": {"decimal": [5, 2]}}},
            {
                "select": {"value": {"ifnull": [{"sum": "film.rental_rate"}, 0]}},
                "into": "v_rentfees",
                "from": ["film", "inventory", "rental"],
                "where": {"and": [
                    {"eq": ["film.film_id", "inventory.film_id"]},
                    {"eq": ["inventory.inventory_id", "rental.inventory_id"]},
                    {"lte": ["rental.rental_date", "p_effective_date"]},
                    {"eq": ["rental.customer_id", "p_customer_id"]},
                ]},
            },
            {
                "select": {"value": {"ifnull": [
                    {"sum": {"if": [
                        {"gt": [
                            {"sub": [{"to_days": "rental.return_date"}, {"to_days": "rental.rental_date"}]},
                            "film.rental_duration",
                        ]},
                        {"sub": [
                            {"sub": [{"to_days": "rental.return_date"}, {"to_days": "rental.rental_date"}]},
                            "film.rental_duration",
                        ]},
                        0,
                    ]}},
                    0,
                ]}},
                "into": "v_overfees",
                "from": ["rental", "inventory", "film"],
                "where": {"and": [
                    {"eq": ["film.film_id", "inventory.film_id"]},
                    {"eq": ["inventory.inventory_id", "rental.inventory_id"]},
                    {"lte": ["rental.rental_date", "p_effective_date"]},
                    {"eq": ["rental.customer_id", "p_customer_id"]},
                ]},
            },
            {
                "select": {"value": {"ifnull": [{"sum": "payment.amount"}, 0]}},
                "into": "v_payments",
                "from": "payment",
                "where": {"and": [
                    {"lte": ["payment.payment_date", "p_effective_date"]},
                    {"eq": ["payment.customer_id", "p_customer_id"]},
                ]},
            },
            {"return": {"sub": [{"add": ["v_rentfees", "v_overfees"]}, "v_payments"]}},
        ]},
    }},
    None,
    {"delimiter": ";"},
    {"delimiter": "$$"},
    {"create_procedure": {
        "name": "film_in_stock",
        "params": [
            {"mode": "in", "name": "p_film_id", "type": {"int": {}}},
            {"mode": "in", "name": "p_store_id", "type": {"int": {}}},
            {"mode": "out", "name": "p_film_count", "type": {"int": {}}},
        ],
        "body": {"block": [
            {
                "select": {"value": "inventory_id"},
                "from": "inventory",
                "where": {"and": [
                    {"eq": ["film_id", "p_film_id"]},
                    {"eq": ["store_id", "p_store_id"]},
                    {"inventory_in_stock": "inventory_id"},
                ]},
            },
            {
                "select": {"value": {"count": "*"}},
                "from": "inventory",
                "where": {"and": [
                    {"eq": ["film_id", "p_film_id"]},
                    {"eq": ["store_id", "p_store_id"]},
                    {"inventory_in_stock": "inventory_id"},
                ]},
                "into": "p_film_count",
            },
        ]},
    }},
    None,
    {"delimiter": ";"},
    {"delimiter": "$$"},
    {"create_procedure": {
        "name": "film_not_in_stock",
        "params": [
            {"mode": "in", "name": "p_film_id", "type": {"int": {}}},
            {"mode": "in", "name": "p_store_id", "type": {"int": {}}},
            {"mode": "out", "name": "p_film_count", "type": {"int": {}}},
        ],
        "body": {"block": [
            {
                "select": {"value": "inventory_id"},
                "from": "inventory",
                "where": {"and": [
                    {"eq": ["film_id", "p_film_id"]},
                    {"eq": ["store_id", "p_store_id"]},
                    {"not": {"inventory_in_stock": "inventory_id"}},
                ]},
            },
            {
                "select": {"value": {"count": "*"}},
                "from": "inventory",
                "where": {"and": [
                    {"eq": ["film_id", "p_film_id"]},
                    {"eq": ["store_id", "p_store_id"]},
                    {"not": {"inventory_in_stock": "inventory_id"}},
                ]},
                "into": "p_film_count",
            },
        ]},
    }},
    None,
    {"delimiter": ";"},
    {"delimiter": "$$"},
    {"create_function": {
        "name": "inventory_held_by_customer",
        "params": {"name": "p_inventory_id", "type": {"int": {}}},
        "returns": {"int": {}},
        "body": {"block": [
            {"declare": {"name": "v_customer_id", "type": {"int": {}}}},
            {"declare_handler": {"action": "exit", "conditions": "not_found", "body": {"return": {"null": {}}}}},
            {
                "select": {"value": "customer_id"},
                "into": "v_customer_id",
                "from": "rental",
                "where": {"and": [{"missing": "return_date"}, {"eq": ["inventory_id", "p_inventory_id"]}]},
            },
            {"return": "v_customer_id"},
        ]},
    }},
    None,
    {"delimiter": ";"},
    {"delimiter": "$$"},
    {"create_function": {
        "name": "inventory_in_stock",
        "params": {"name": "p_inventory_id", "type": {"int": {}}},
        "returns": {"boolean": {}},
        "body": {"block": [
            {"declare": {"name": "v_rentals", "type": {"int": {}}}},
            {"declare": {"name": "v_out", "type": {"int": {}}}},
            {
                "select": {"value": {"count": "*"}},
                "into": "v_rentals",
                "from": "rental",
                "where": {"eq": ["inventory_id", "p_inventory_id"]},
            },
            {"if": {"eq": ["v_rentals", 0]}, "then": {"return": True}},
            {
                "select": {"value": {"count": "rental_id"}},
                "into": "v_out",
                "from": ["inventory", {"left join": "rental", "using": "inventory_id"}],
                "where": {"and": [
                    {"eq": ["inventory.inventory_id", "p_inventory_id"]},
                    {"missing": "rental.return_date"},
                ]},
            },
            {"if": {"gt": ["v_out", 0]}, "then": {"return": False}, "else": {"return": True}},
        ]},
    }},
    None,
    {"delimiter": ";"},
    {"set": {"sql_mode": "@old_sql_mode"}},
    {"set": {"foreign_key_checks": "@old_foreign_key_checks"}},
    {"set": {"unique_checks": "@old_unique_checks"}},
]
