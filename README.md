Simple Python VM
----------------

This project is the code for the blog post at https://csl.name/post/vm/.

It contains a simple Forth-like VM written in Python. It also contains a
very simple peephole-optimizer that does constant folding (and ignoring the
fact that jumps are then off).

It's an educational project.

Example
-------

Here's code to print the Fibonacci sequence:

    : println dup . ;
    : next swap over + ;

    # Start values
    0 println
    1 println

    # Loop forever
    @ next println return

You can run it by typing:

    python vm.py examples/fibonacci.source | head -20

More examples in the `examples/` folder.
