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


Example: Running a simple program from Python
---------------------------------------------

    from crianza import *

    source = "2 3 + 4 *" # or: (2+3) * 4

    code = parse(source)
    machine = Machine(code)
    machine.run()

    assert(machine.top == 20)

The source code is very much like
[Forth](https://en.wikipedia.org/wiki/Forth_(programming_language)).

You can also do some simple optimizations on the code by specifying:

    code = check(optimize(parse(sourc)))

In this case, the entire code will be constant-folded to simply 20. The `check`
function checks for simple errors.


Example: Source code with subroutines
-------------------------------------

Here's code to print the Fibonacci sequence:

    : println dup . ;
    : next swap over + ;

    # Start values
    0 println
    1 println

    # Loop forever
    @ next println return

You can run it by typing:

    crianza fibonacci.source | head -20

More examples in the `examples/` folder.


License and author
------------------

Copyright (C) 2015 Christian Stigen Larsen
Open source license; see the LICENSE file.

