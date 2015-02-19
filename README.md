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

The simplest way to get started with the language itself is to use the `eval`
function:

    >>> import crianza
    >>> crianza.eval("2 3 + 4 *")
    <Machine: ip=1 |ds|=1 |ds|=0 top=20>

This is equivalent of computing `(2 + 3) * 4` and puts the result on top of the
data stack.  We can get this by doing `crianza.eval(...).top`.  The language is
basically [dialect of
Forth](https://en.wikipedia.org/wiki/Forth_(programming_language)).

The above code is automatically optimized.  In fact, it's constant-folded down
to the result `20`:

    >>> m = crianza.eval("2 3 + 4 *")
    >>> m.code
    [20]

You can also divert program output to a memory buffer:

    >>> from StringIO import StringIO
    >>> buffer = StringIO()
    >>> machine = crianza.eval('"Hello, world!" .', output=buffer)
    >>> buffer.getvalue()
    'Hello, world!\n'
    >>> machine.code_string
    '"Hello, world!" .'

The more elaborate way of doing this is:

    from crianza import *

    source = "2 3 + 4 *" # or: (2+3) * 4

    code = parse(source)
    machine = Machine(code)
    machine.run()

    assert(machine.top == 20)

You can also do some simple optimizations on the code by specifying:

    code = compile(source, optimize=True)

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

