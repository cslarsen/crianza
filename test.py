from operator import *
import unittest

from vm import Machine, constant_fold, MachineError, CompilationError, optimize

class TestVM(unittest.TestCase):
    def _Machine(self, *args):
        return Machine(*args, output=None)

    def _run(self, *machine_args):
        """Runs machine and returns it."""
        return self._Machine(*machine_args).run()

    def test_initial_conditions(self):
        self.assertEqual(self._run([]).stack, [])

    def _test_arithmetic(self, a, b, op):
        self.assertEqual(self._run([a, b, op.__name__]).stack, [op(a,b)])

    def test_stack(self):
        self.assertEqual(self._run([1,2,3,4,5,"*","*","*","*"]).stack, [120])
        self.assertEqual(self._run([1,2,3,4,5,"-","-","-","-"]).stack, [3])
        self.assertEqual(self._run([1,2,3,4,5,"+","+","+","+"]).stack, [15])

    def test_arithmetic(self):
        ops = [mul, add]
        for a in range(-10,10):
            for b in range(-10,10):
                for op in ops:
                    self._test_arithmetic(a, b, op)

    def test_optimizer_errors(self):
        for op in ["/", "mod", "div", "%"]:
            with self.assertRaises(CompilationError):
                constant_fold([2, 0, op], ignore_errors=False)

    def test_optimizer(self):
        self.assertEqual(constant_fold([2,3,"*","."]), [6,"."])
        self.assertEqual(constant_fold([2,2,3,"*","."]), [2,6,"."])
        self.assertEqual(constant_fold([5,2,3,"*","+","."]), [11,"."])
        self.assertEqual(constant_fold([5,2,3,"*","+",4,"*","."]), [44,"."])
        self.assertEqual(constant_fold([2, 3, "+", 5, "*", "println"]),
                [25, "println"])
        self.assertEqual(constant_fold([10, "dup"]), [10, 10])
        self.assertEqual(constant_fold([1, 2, "dup", "dup", "+", "+"]), [1, 6])
        self.assertEqual(constant_fold([1, 2, 3, "swap"]), [1, 3, 2])
        self.assertEqual(constant_fold([1, 2, 3, "drop", "drop"]), [1])


if __name__ == "__main__":
    unittest.main()
