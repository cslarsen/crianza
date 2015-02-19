Crianza
-------

Crianza is a very simple program virtual machine with example genetic
programming applications.

It contains the code from the blog post at https://csl.name/post/vm/

The VM contains:

  * An interpreter for a Forth-like stack-based language
  * Some simple peephole optimizations
  * Simple correctness checking
  * Compilation from source language down to machine language

The genetic programming part uses a simple evolutionary approach with crossover
and weighted Tanimoto coefficients to relate fitness scores.

The project's main goal is to be tutorial and fun.

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
