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
basically a [dialect of
Forth](https://en.wikipedia.org/wiki/Forth_(programming_language)).

The complete machine is returned.  Here it prints the current value of the
instruction pointer `ip`, the number of items on the data stack (`|ds|`), the
number of items on the return stack (`|rs|`) and the value on top of the stack.

`eval` will automatically optimize the code.  In this case, the entire
expression is constant-folded down to the result `20`:

    >>> m = crianza.eval("2 3 + 4 *")
    >>> m.code
    [20]

You can divert program output to a memory buffer:

    >>> from StringIO import StringIO
    >>> buffer = StringIO()
    >>> machine = crianza.eval('"Hello, world!" .', output=buffer)
    >>> buffer.getvalue()
    'Hello, world!\n'
    >>> machine.code_string
    '"Hello, world!" .'

Example: Controlling parsing
----------------------------

The more elaborate way of parsing and running code is:

    from crianza import *

    source = "2 3 + 4 *" # or: (2+3) * 4

    code = compile(parse(source), optimize=False)
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


Example: Genetic programming
----------------------------

Crianza also contains very simple genetic programming facilities, just to
demonstrate a cool usage of the VM.

You can run the example simulation, which simply attempts to find a program
that squares input numbers.  For speed, you should run it with `pypy`:

    $ pypy -OO examples/genetic/square-number.py
    Starting ...
    gen 1 1-fitness 0.410299299627 avg code len 10.00 avg stack len 0.00
    gen 2 1-fitness 0.400844361878 avg code len 6.20 avg stack len 0.00
    gen 3 1-fitness 0.417903405823 avg code len 5.20 avg stack len 0.00
    gen 4 1-fitness 0.403448229584 avg code len 4.60 avg stack len 0.00
    gen 5 1-fitness 0.405436543540 avg code len 2.80 avg stack len 0.00
    gen 6 1-fitness 0.359110672048 avg code len 2.20 avg stack len 0.80
    gen 7 1-fitness 0.206176614950 avg code len 1.60 avg stack len 1.00
    gen 8 1-fitness 0.028440428102 avg code len 2.80 avg stack len 2.20
    gen 9 1-fitness 0.000000044595 avg code len 3.00 avg stack len 1.40
    gen 10 1-fitness 0.000000000833 avg code len 2.20 avg stack len 1.20
    gen 11 1-fitness 0.000000000000 avg code len 2.00 avg stack len 1.00

    Listing programs from best to worst, unique solutions only.
    0 <Machine: ip=3 |ds|=1 |ds|=0 top=8281>: dup *

    The GP found that you can make a square word like so:

        : square
            dup * ;

    Example output:

        850 square ==> 722500
        702 square ==> 492804
        177 square ==> 31329
        803 square ==> 644809
        786 square ==> 617796

    The code seems to be correct.

It uses a weighted [Tanimoto coefficient (or Jaccard
index)](https://en.wikipedia.org/wiki/Jaccard_index#Tanimoto_similarity_and_distance)
to relate fitness scores among programs, so you can encode any goal. See the
example files for more information.

Here is the main part of the code that instructs Crianza to find a
`square-number` subroutine (see the file `examples/genetic/square-number.py`).

    def score(self):
        # Goals, what kind of program we want to evolve ...
        wanted = (
            self._input**2, # Find a way to calculate n^2
            0,              # We don't want errors
            1,              # Don't put a lot of values on the data stack
            0,              # The return stack should be zero after completion
            0)              # Code should be as small as possible, but not over
                            # 5 opcodes (see below on how to encode this goal)

        # ... and the goals corresponding weights
        weights = (0.10, 0.80, 0.02, 0.02, 0.06)

        # Which values we actually got (and how they can be converted to
        # numbers) ...
        actual = (self.top if vm.isnumber(self.top) else 9999.9,
                  1000 if self._error else 0,
                  len(self.stack),
                  len(self.return_stack),
                  len(self.code) if len(self.code)<5 else 999)

        # Return a value from 0.0 (perfect score) to 1.0 (infinitely bad score)
        return 1.0 - weighted_tanimoto(actual, wanted, weights)

For the above example, the fitness score encodes several goals:

  * The top of the stack `top` should equal the square of the program's input `self._input**2`.
  * Runtime and compile time errors in the program are penalized (`1000 if self._error else 0`).
  * The length of the data stack should be exactly one (this makes it easier to embed the resulting code in a subroutine).
  * The return stack should be zero after program completion.
  * The code length should be no more than 5 instructions, but as small as possible.

For the above, it almost always seems to converge. The obvious result for
calculating the square of a number is `dup *`, and this is what I usually get,
although I've also gotten fun variants that are almost correct, such as `dup
abs *`.

I've not played around much with the GP, but I think it currently does
crossover quite badly and unintelligently.  It also seems to have problems
converging on somewhat more advanced programs. But, it's a start, and it's
definitely a lot of fun!

License and author
------------------

Copyright (C) 2015 Christian Stigen Larsen

See the LICENSE file for terms.

