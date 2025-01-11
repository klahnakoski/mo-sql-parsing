# More SQL Parsing Tests

The test suite has over 400 tests.

## Running Tests

For __Linux__:

	git clone https://github.com/klahnakoski/mo-sql-parsing.git
	cd mo-sql-parsing
	pip install -r requirements.txt
	pip install -r tests/requirements.txt
    export PYTHONPATH=.	
	python -m unittest discover .

 For __Windows__:

	pip install -r requirements.txt
    pip install -r tests\requirements.txt
    set PYTHONPATH=.    
    python.exe -m unittest discover .

### Debugging Suggestions

Once you have written a failing test, you can use `with Debugger():` in your test to print out a trace of matching attempts. 
 
## History

* **November 2021** - added basic DML statements
* **October 2021** - handle `select distinct on` and change parsing of `select distinct`, again.
* **September 2021** - added option for `{"op": op, "args":args}` form
* **August 2021** - good work of ykawakamy added  [create table](https://github.com/klahnakoski/mo-sql-parsing/pull/16) syntax
* **June 2021** - moved to `mo-sql-parsing`
* **November 2020** - Add `pip install` tests
* **October 2020** - Use mo-parsing for less recursion and faster parsing 
* **January 2018** - fixes for Python3
* **July 2017** - Add suite to start testing error messages, with hope of improving them
* **April 2017** - All tests pass
* **March 2017** - Added a number of test cases, most of which are missing the expected JSON parse tree, so they fail.


