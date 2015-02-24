PYTHONPATH := PYTHONPATH=.:$$PYTHONPATH
PYTHON := $(PYTHONPATH) pypy
CRIANZA := $(PYTHONPATH) bin/crianza

default: test

repl:
	@$(PYTHONPATH) bin/crianza --repl

test:
	$(PYTHON) tests/test.py -v

test-genetic:
	$(PYTHON) examples/genetic/double-number.py
	$(PYTHON) examples/genetic/square-number.py

test-examples:
	$(CRIANZA) examples/fibonacci.source | head -15

check: test test-examples test-genetic

lint:
	pyflakes \
		crianza/*.py \
		tests/*.py \
		examples/genetic/*.py

clean:
	find . -name '*.pyc' -exec rm -f {} \;
