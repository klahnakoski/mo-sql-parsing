# encoding: utf-8
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at https://www.mozilla.org/en-US/MPL/2.0/.
#
# Author: Kyle Lahnakoski (kyle@lahnakoski.com)
#
from time import time
import mo_imports

# ensure first import is fast
start_import = time()
from mo_sql_parsing import format

end_time = time()
print(format({"from": "a"}))
for e in mo_imports._expectations:
    print((object.__getattribute__(e, "module"), object.__getattribute__(e, "name")))

if mo_imports._monitor:
    raise Exception("mo_imports._monitor should not be alive")
