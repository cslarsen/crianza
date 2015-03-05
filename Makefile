PYTHONPATH := PYTHONPATH=.:$$PYTHONPATH
CRIANZA := $(PYTHONPATH) bin/crianza

# Tip: Try changing "python" to "pypy"
PYTHON := $(PYTHONPATH) python

default: test

repl:
	@$(PYTHONPATH) bin/crianza --repl

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

setup-pypi-test:
	python setup.py register -r pypitest
	python setup.py sdist upload -r pypitest

setup-pypi-publish:
	python setup.py register -r pypi
	python setup.py sdist upload --sign -r pypi

lint:
	pyflakes \
		crianza/*.py \
		tests/*.py \
		examples/genetic/*.py

clean:
	find . -name '*.pyc' -exec rm -f {} \;
