# More SQL Parsing Tests

The test suite has over 1200 tests.

## Running Tests

For __Linux__:

	git clone https://github.com/klahnakoski/mo-sql-parsing.git
	cd mo-sql-parsing
    python -m venv .venv
    source .venv/bin/activate
	python -m pip install --no-deps -r tests/requirements.lock
    python -m pip install --upgrade -r packaging/requirements.txt
	python -m unittest discover .

 For __Windows__:

	git clone https://github.com/klahnakoski/mo-sql-parsing.git
	cd mo-sql-parsing
    python -m venv .venv
    .venv\Scripts\activate
    python -m pip install --no-deps-r tests\requirements.lock
	python -m pip install --upgrade -r packaging\requirements.txt
    python -m unittest discover .

### Debugging Suggestions

Once you have written a failing test, you can use `with Debugger():` in your test to print out a trace of matching attempts. 

### Upgrade dependencies

To upgrade the test dependencies, run:

    .venv\Scripts\activate
    python -m pip install --upgrade pip-tools
    pip-compile tests/requirements.txt -o tests/requirements.lock


