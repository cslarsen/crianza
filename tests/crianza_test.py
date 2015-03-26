try:
    import StringIO
except ImportError:
    from io import StringIO

import crianza
import operator
import random
import sys
import unittest

try:
    import crianza.native
    CRIANZA_NATIVE = True
except ImportError:
    CRIANZA_NATIVE = False

fibonacci_source = \
"""
# The Fibonacci Sequence

: println dup . ;
: next swap over + ;

# Start values
0 println
1 println

# Loop forever
@ next println return
"""

class TestCrianza(unittest.TestCase):
    def test_initial_conditions(self):
        machine = crianza.Machine([])
        machine.run()
        self.assertEqual(machine.data_stack, crianza.Stack([]))
        self.assertEqual(machine.return_stack, crianza.Stack([]))
        self.assertEqual(machine.stack, [])
        self.assertEqual(machine.instruction_pointer, 0)
        self.assertEqual(machine.code, [])
        self.assertEqual(machine.input, sys.stdin)
        self.assertEqual(machine.output, sys.stdout)

    def test_eval(self):
        self.assertEqual(crianza.eval("1 2 3 4 5 * * * *"), 120)
        self.assertEqual(crianza.eval("1 2 3 4 5 - - - -"), 3)
        self.assertEqual(crianza.eval("1 2 3 4 5 + + + +"), 15)

    def test_parser(self):
        test = lambda src, tokens: self.assertEqual(crianza.parse(src), tokens)
        test("1", [1])
        test("1 2", [1, 2])
        test("123 dup * .", [123, "dup", "*", "."])
        test("1 2 3 4 5 * * * *", [1, 2, 3, 4, 5, "*", "*", "*", "*"])
        test(": square\n\tdup * ;\n\n12 square .\n", [":", "square", "dup", "*",
            ";", 12, "square", "."])

    def _test_arithmetic(self, a, b, op):
        name = {"mul": "*",
                "sub": "-",
                "add": "+",
                "mod": "%",
                "div": "/"}[op.__name__]

        source = "%d %d %s" % (a, b, name)
        self.assertEqual(crianza.eval(source), op(a, b))

    def test_random_arithmetic(self):
        ops = [operator.mul, operator.add]
        for op in ops:
            for _ in xrange(100):
                # TODO: Add negative numbers when our parser supports it
                a = random.randint(0, +(2**31-1))
                b = random.randint(0, +(2**31-1))
                self._test_arithmetic(a, b, op)

    def test_optimizer_errors(self):
        for op in [crianza.instructions.div, crianza.instructions.mod]:
            instr = crianza.instructions.lookup(op)
            func = lambda: crianza.constant_fold([2, 0, instr], ignore_errors=False)
            self.assertRaises(crianza.CompileError, func)

    def test_optimizer(self):
        self.assertEqual(crianza.constant_fold([2,3,"*","."]), [6, "."])
        self.assertEqual(crianza.constant_fold([2,2,3,"*","."]), [2, 6, "."])
        self.assertEqual(crianza.constant_fold([5,2,3,"*","+","."]), [11, "."])
        self.assertEqual(crianza.constant_fold([5,2,3,"*","+",4,"*","."]), [44, "."])
        self.assertEqual(crianza.constant_fold([2,3,"+",5,"*","write"]), [25, "write"])
        self.assertEqual(crianza.constant_fold([10, "dup"]), [10, 10])
        self.assertEqual(crianza.constant_fold([1,2,"dup","dup","+","+"]), [1,6])
        self.assertEqual(crianza.constant_fold([1,2,3,"swap"]), [1,3,2])
        self.assertEqual(crianza.constant_fold([1,2,3,"drop","drop"]), [1])
        self.assertEqual(crianza.constant_fold([1, 123, "str"]), [1, "123"])
        self.assertEqual(crianza.constant_fold([1, "112", "int"]), [1, 112])
        self.assertEqual(crianza.constant_fold([1, 123, "str", "int"]), [1, 123])

    def test_program_fibonacci(self):
        code = crianza.compile(crianza.parse(fibonacci_source))
        # TODO: Unembed this:
        #self.assertEqual(code, native_types([0, 13, 'call', 1,
        #    13, 'call', '@', 16, 'call', 13, 'call', 'return', 'exit', 'dup',
        #    '.', 'return', 'swap', 'over', '+', 'return']))

        machine = crianza.Machine(code, output=None)

        # skip to main loop
        machine.run(11)

        sequence = []
        numbers_to_generate = 15

        for its in xrange(0, numbers_to_generate):
            sequence.append(machine.top)
            machine.run(13) # next number

        self.assertEqual(sequence, [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144,
            233, 377, 610])

    def test_io(self):
        fin = StringIO.StringIO("Input line 1.\nInput line 2.")
        fout = StringIO.StringIO()
        result = crianza.eval('123 read "howdy" . .', input=fin, output=fout)
        self.assertEqual(result, 123)
        self.assertEqual(fin.getvalue()[fin.tell():], "Input line 2.")
        self.assertEqual(fout.getvalue(), "howdy\nInput line 1.\n")

    def _execfile(self, filename, input=StringIO.StringIO(),
            output=StringIO.StringIO(), steps=1000):
        with open(filename, "rt") as f:
            return crianza.execute(f, input=input, output=output, steps=steps)

    def test_program_even_odd(self):
        fin = StringIO.StringIO("1\n2\n3\n")
        fout = StringIO.StringIO()
        m = self._execfile("tests/even-odd.source", input=fin, output=fout)
        self.assertEqual(fout.getvalue(),
            "Enter a number: The number 1 is odd.\n" +
            "Enter a number: The number 2 is even.\n" +
            "Enter a number: The number 3 is odd.\n" +
            "Enter a number: ")
        self.assertEqual(fin.tell(), len(fin.getvalue()))
        self.assertEqual(m.top, "")
        self.assertEqual(m.stack, [""])
        self.assertEqual(m.return_stack, crianza.Stack([]))

    def test_program_sum_mul_1(self):
        fout = StringIO.StringIO()
        m = self._execfile("tests/sum-mul-1.source", output=fout)
        self.assertEqual(fout.getvalue(), "(2+3) * 4 = 20\n")
        self.assertEqual(m.top, None)
        self.assertEqual(m.stack, [])
        self.assertEqual(m.return_stack, crianza.Stack([]))

    def test_program_sum_mul_2(self):
        fin = StringIO.StringIO("12\n34\n")
        fout = StringIO.StringIO()
        m = self._execfile("tests/sum-mul-2.source", input=fin, output=fout)
        self.assertEqual(fout.getvalue(),
                "Enter a number: " +
                "Enter another number: " +
                "Their sum is: 46\n" +
                "Their product is: 408\n")
        self.assertEqual(m.top, None)
        self.assertEqual(m.stack, [])
        self.assertEqual(m.return_stack, crianza.Stack([]))

    def test_program_subroutine_1(self):
        fout = StringIO.StringIO()
        m = self._execfile("tests/subroutine-1.source", output=fout)
        self.assertEqual(fout.getvalue(), "one\ntwo\nthree\n144\nfinished\n")
        self.assertEqual(m.top, 0)
        self.assertEqual(m.stack, ["one", "two", "three", 144, 0])
        self.assertEqual(m.return_stack, crianza.Stack([]))

    def test_program_fibonacci_1(self):
        fout = StringIO.StringIO()
        m = self._execfile("tests/fibonacci.source", output=fout, steps=100)
        self.assertEqual(fout.getvalue(),
            "0\n1\n1\n2\n3\n5\n8\n13\n21\n34\n55\n89\n144\n233\n377\n")
        self.assertEqual(m.top, 610)
        self.assertEqual(m.stack, [377, 610])
        self.assertEqual(m.return_stack, crianza.Stack([]))

    def test_program_fibonacci_2(self):
        fout = StringIO.StringIO()
        m = self._execfile("tests/fibonacci-2.source", output=fout, steps=180)
        self.assertEqual(fout.getvalue(),
            "0\n1\n1\n2\n3\n5\n8\n13\n21\n34\n55\n89\n144\n233\n377\n")
        self.assertEqual(m.top, 377)
        self.assertEqual(m.stack, [233, 377])
        self.assertEqual(m.return_stack, crianza.Stack([6]))


class TestCrianzaNative(unittest.TestCase):
    @unittest.skipUnless(CRIANZA_NATIVE, "crianza.native unsupported")
    def test_mul2(self):
        mul2 = crianza.native.compile([2,"*"], args=1, name="mul2",
                docstring="Multiplies number with two.")

        self.assertIsNotNone(mul2)
        self.assertEqual(mul2.__doc__, "Multiplies number with two.")
        self.assertEqual(mul2.__name__, "mul2")

        for n in xrange(100):
            self.assertEqual(n*2, mul2(n))

        for __ in range(10):
            n = random.randint(-1000000, 1000000)
            self.assertEqual(n*2, mul2(n))


if __name__ == "__main__":
    unittest.main()
