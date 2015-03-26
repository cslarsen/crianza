
Crianza
-------

Crianza is a very simple program virtual machine with example genetic
programming applications.

It comes both with a command line program (for running programs and starting a
REPL) and as a Python module so you can create and run programs from Python.
The ``crianza.genetic`` module contains a simple genetic programming framework.

This project originated from a blog post I wrote at https://csl.name/post/vm/
(it details how you can write your own interpreter from scratch) and is hosted
on https://github.com/cslarsen/crianza

The VM contains:

-  An interpreter for a Forth-like stack-based language
-  Some simple peephole optimizations
-  Simple correctness checking
-  Compilation from source language down to virtual machine language
-  Threaded code interpretation
-  Data types: Integers, floats, booleans and strings
-  An experimental, in-progress compiler to native Python bytecode

The genetic programming part uses a simple evolutionary approach with
crossover and weighted Tanimoto coefficients to relate fitness scores.

The project's main goal is to be tutorial and fun.

Installing
----------

Install from PyPI::

    $ pip install crianza

or from the repository::

    $ git clone https://github.com/cslarsen/crianza.git
    $ cd crianza
    $ python setup.py install

Example: Using crianza from the command line
--------------------------------------------

Just type ``crianza -r`` or ``crianza --repl`` to start the interpreter.  In
this example, we want to calculate ``(2+3)*4``::

    $ crianza -r
    Extra commands for the REPL:
    .code    - print code
    .raw     - print raw code
    .quit    - exit immediately
    .reset   - reset machine (IP and stacks)
    .restart - create a clean, new machine
    .clear   - same as .restart
    .stack   - print data stack

    > 2 3 + 4 * .
    Optimizer: Constant-folded 2 3 + to 5
    Optimizer: Constant-folded 5 4 * to 20
    20
    > .code
    IP: 2
    DS: []
    RS: []
    0000  20 .
    >

Notice that the optimizer constant-folds the entire expression down to simply
``20``.  You can see this by printing out the compiled code with the command
``.code``.  This will list the current instruction pointer ``IP``, the number
of items on the data stack ``DS`` and the return stack ``RS`` followed by the
code.

You can run programs in files as well.  Use ``crianza -h`` to get options.

Example: Running a simple program from Python
---------------------------------------------

The simplest way to get started with the language itself is to use the
``eval`` function:

::

    >>> import crianza
    >>> crianza.eval("2 3 + 4 *")
    20

You can also use ``crianza.execute`` to get the machine used to execute
the program:

::

    >>> crianza.execute("2 3 + 4 *")
    <Machine: ip=1 |ds|=1 |ds|=0 top=20>

This is equivalent of computing ``(2 + 3) * 4`` and puts the result on
top of the data stack. We can get this by doing
``crianza.execute(...).top`` or just use ``crianza.eval``. The language
is basically a `dialect of
Forth <https://en.wikipedia.org/wiki/Forth_(programming_language)>`_.

The complete machine is returned. Here it prints the current value of
the instruction pointer ``ip``, the number of items on the data stack
(``|ds|``), the number of items on the return stack (``|rs|``) and the
value on top of the stack.

``eval`` and ``execute`` will automatically optimize the code (turn off
with the option ``optimize=False``). In this case, the entire expression
is constant-folded down to the result ``20``:

::

    >>> m = crianza.execute("2 3 + 4 *")
    >>> m.code
    [20]

You can divert program output to a memory buffer:

::

    >>> from StringIO import StringIO
    >>> buffer = StringIO()
    >>> machine = crianza.execute('"Hello, world!" .', output=buffer)
    >>> buffer.getvalue()
    'Hello, world!\n'
    >>> machine.code_string
    '"Hello, world!" .'

Example: Controlling parsing
----------------------------

The more elaborate way of parsing and running code is:

::

    from crianza import *

    source = "2 3 + 4 *" # or: (2+3) * 4

    code = compile(parse(source), optimize=False)
    machine = Machine(code)
    machine.run()

    assert(machine.top == 20)

You can also do some simple optimizations on the code by specifying:

::

    code = compile(source, optimize=True)

In this case, the entire code will be constant-folded to simply 20. The
``check`` function checks for simple errors.

Example: Source code with subroutines
-------------------------------------

Here's code to print the Fibonacci sequence:

::

    : println dup . ;
    : next swap over + ;

    # Start values
    0 println
    1 println

    # Loop forever
    @ next println return

You can run it by typing:

::

    crianza fibonacci.source | head -20

More examples in the ``examples/`` folder.

Example: Genetic programming
----------------------------

Crianza also contains very simple genetic programming facilities, just
to demonstrate a cool usage of the VM.

You can run the example simulation, which simply attempts to find a
program that squares input numbers. For speed, you should run it with
``pypy``:

::

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

It uses a weighted `Tanimoto coefficient (or Jaccard
index) <https://en.wikipedia.org/wiki/Jaccard_index#Tanimoto_similarity_and_distance>`_
to relate fitness scores among programs, so you can encode any goal. See
the example files for more information.

Here is the main part of the code that instructs Crianza to find a
``square-number`` subroutine (see the file
``examples/genetic/square-number.py``).

::

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

-  The top of the stack ``top`` should equal the square of the program's
   input ``self._input**2``.
-  Runtime and compile time errors in the program are penalized
   (``1000 if self._error else 0``).
-  The length of the data stack should be exactly one (this makes it
   easier to embed the resulting code in a subroutine).
-  The return stack should be zero after program completion.
-  The code length should be no more than 5 instructions, but as small
   as possible.

For the above, it almost always seems to converge. The obvious result
for calculating the square of a number is ``dup *``, and this is what I
usually get, although I've also gotten fun variants that are almost
correct, such as ``dup abs *``.

I've not played around much with the GP, but I think it currently does
crossover quite badly and unintelligently. It also seems to have
problems converging on somewhat more advanced programs. But, it's a
start, and it's definitely a lot of fun!

Native Python bytecode compiler
-------------------------------

Crianza also contains ``crianza.native``, an experimental, work-in-progress
compiler to native CPython bytecode. At the moment, it only correctly
implements simple instructions and doesn't do any optimizations.

Furthermore, it uses the `byteplay module
<https://pypi.python.org/pypi/byteplay/0.2>`_, which works for Python 2.x only.
In time, I plan to support all instructions and the Python 3.x series.

To test it, you can do::

    >>> import crianza.native
    >>> mul2 = crianza.native.compile([2, "*"], args=1)
    >>> mul2(101)
    202
    >>> import dis
    >>> dis.dis(mul2)
      1           0 LOAD_FAST                0 (arg0)
                  3 LOAD_CONST               1 (2)
                  6 BINARY_MULTIPLY
                  7 RETURN_VALUE

The ``crianza.native.compile`` function takes in source code and ``args``, the
number of arguments the resulting Python function will take.  In the above
example, we create a function that multiplies arguments by two, hence
``args=1``.  This is _exactly_ the same as doing::

    >>> py_mul2 = lambda n: n*2
    >>> dis.dis(py_mul2)
      1           0 LOAD_FAST                0 (n)
                  3 LOAD_CONST               1 (2)
                  6 BINARY_MULTIPLY
                  7 RETURN_VALUE

In fact, the Python bytecode for the two functions are exactly the same, sans
the local argument name.

Because the CPython bytecode also operates on Python types, it naturally
supports things like multiplying sequences::

    >>> mul2("hello")
    'hellohello'

and equivalently,

::
    >>> py_mul2("hello")
    'hellohello'

Again, note that the compiler is currently *very* buggy. In particular, it
doesn't correctly implement branching (jumps, if-statements, etc.) and doesn't
have support for strings.

License and author
------------------

Copyright (C) 2015 Christian Stigen Larsen

Distributed under the BSD 3-Clause License. See the LICENSE.txt file for
the full text.
