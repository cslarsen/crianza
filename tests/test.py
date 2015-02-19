import operator
import unittest
from crianza import vm

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

class TestVM(unittest.TestCase):
    def _Machine(self, *args):
        return vm.Machine(*args, output=None)

    def _run(self, *machine_args):
        """Runs machine and returns it."""
        return self._Machine(*machine_args).run()

    def test_initial_conditions(self):
        self.assertEqual(self._run([]).stack, [])

    def _test_arithmetic(self, a, b, op):
        translate = {"mul": "*",
                     "sub": "-",
                     "add": "+",
                     "mod": "%",
                     "div": "/"}
        self.assertEqual(self._run([a, b, translate[op.__name__]]).stack, [op(a,b)])

    def test_stack(self):
        self.assertEqual(self._run([1,2,3,4,5,"*","*","*","*"]).stack, [120])
        self.assertEqual(self._run([1,2,3,4,5,"-","-","-","-"]).stack, [3])
        self.assertEqual(self._run([1,2,3,4,5,"+","+","+","+"]).stack, [15])

    def test_arithmetic(self):
        ops = [operator.mul, operator.add]
        for a in range(-10,10):
            for b in range(-10,10):
                for op in ops:
                    self._test_arithmetic(a, b, op)

    def test_optimizer_errors(self):
        for op in ["/", "%"]:
            func = lambda: vm.constant_fold([2, 0, op], ignore_errors=False)
            self.assertRaises(vm.CompilationError, func)

    def test_optimizer(self):
        self.assertEqual(vm.constant_fold([2,3,"*","."]), [6,"."])
        self.assertEqual(vm.constant_fold([2,2,3,"*","."]), [2,6,"."])
        self.assertEqual(vm.constant_fold([5,2,3,"*","+","."]), [11,"."])
        self.assertEqual(vm.constant_fold([5,2,3,"*","+",4,"*","."]), [44,"."])
        self.assertEqual(vm.constant_fold([2, 3, "+", 5, "*", "println"]),
                [25, "println"])
        self.assertEqual(vm.constant_fold([10, "dup"]), [10, 10])
        self.assertEqual(vm.constant_fold([1, 2, "dup", "dup", "+", "+"]), [1, 6])
        self.assertEqual(vm.constant_fold([1, 2, 3, "swap"]), [1, 3, 2])
        self.assertEqual(vm.constant_fold([1, 2, 3, "drop", "drop"]), [1])

    def test_program_fibonacci(self):
        code = vm.compile(vm.parse(fibonacci_source))
        self.assertEqual(code, [0, 13, 'call', 1, 13, 'call', '@', 16, 'call',
            13, 'call', 'return', 'exit', 'dup', '.', 'return', 'swap', 'over',
            '+', 'return'])

        machine = vm.Machine(code, output=None, optimize=False)

        # skip to main loop
        machine.run(11)

        sequence = []
        numbers_to_generate = 15

        for its in xrange(0, numbers_to_generate):
            sequence.append(machine.top)
            machine.run(13) # next number

        self.assertEqual(sequence, [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144,
            233, 377, 610])

if __name__ == "__main__":
    unittest.main()
