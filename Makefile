PYPATH := PYTHONPATH=.:$$PYTHONPATH
CRIANZA := $(PYPATH) bin/crianza

# Tip: Try changing "python" to "pypy"
PYTHON := $(PYPATH) python

default: test

repl:
	@$(PYPATH) bin/crianza --repl

test:
	$(PYTHON) tests/crianza_test.py -v

test-genetic:
	$(PYTHON) examples/genetic/double-number.py
	$(PYTHON) examples/genetic/square-number.py

test-examples:
	$(CRIANZA) examples/fibonacci.source | head -15 | tr '\n' ' '; echo ""

check: test test-examples test-genetic

setup-test:
	python setup.py test

publish:
	python setup.py bdist_wheel
	gpg --detach-sign -a dist/*.whl
	twine upload dist/*

tox:
	unset PYTHONPATH && tox

lint:
	pyflakes \
		crianza/*.py \
		tests/*.py \
		examples/genetic/*.py

clean:
	find . -name '*.pyc' -exec rm -f {} \;
