# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from time import time

# ensure first import is fast
start_import = time()
from mo_sql_parsing import parse, normal_op
end_time = time()
import_time = end_time-start_import
if import_time > 0.2:
    raise Exception(f"importing mo_sql_parsing took too long ({import_time} seconds)")

# comprehensive import is done on first call
sql = "select trim(' ' from b+c)"
start_run = time()
result = parse(sql, calls=normal_op)
end_run = time()
run_time = end_run-start_run

print(result)
print(f"done in {run_time} seconds")
