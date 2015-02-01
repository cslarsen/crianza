Simple Python VM
----------------

This project is the code for the blog post at https://csl.name/post/vm/.

It contains a simple Forth-like VM written in Python. It also contains a
very simple peephole-optimizer that does constant folding (and ignoring the
fact that jumps are then off).

It's an educational project.

Example
-------

    python vm.py examples/fibonacci.source | head -20

