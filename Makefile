default: test

repl:
	python vm.py

test:
	python test.py -v

lint:
	pyflakes vm.py genetic.py

clean:
	rm -f *.pyc
