PYTHONPATH := PYTHONPATH=.:$$PYTHONPATH
PYTHON := $(PYTHONPATH) pypy
CRIANZA := $(PYTHONPATH) bin/crianza

default: test

repl:
	$(PYTHONPATH) bin/crianza --repl

test:
	$(PYTHON) tests/test.py -v

test-genetic:
	$(PYTHON) examples/genetic/double-number.py
	$(PYTHON) examples/genetic/square-number.py

test-examples:
	(echo 1; echo 2; echo 3) | $(CRIANZA) examples/language/even-odd.source
	$(CRIANZA) examples/language/fibonacci.source | head -15
	$(CRIANZA) examples/language/fibonacci-2.source | head -15
	$(CRIANZA) examples/language/subroutine-1.source
	$(CRIANZA) examples/language/sum-mul-1.source
	(echo 11; echo 22) | $(CRIANZA) examples/language/sum-mul-2.source

check: test test-examples test-genetic

lint:
	pyflakes \
		crianza/*.py \
		tests/*.py \
		examples/genetic/*.py

clean:
	find . -name '*.pyc' -exec rm -f {} \;
