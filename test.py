from operator import *
import unittest

from vm import Machine, constant_fold

class TestVM(unittest.TestCase):
    def test_initial_conditions(self):
        self.assertEqual(Machine([]).run().stack, [])

    def _test_arithmetic(self, a, b, op):
        self.assertEqual(Machine([a, b, op.__name__]).run().stack, [op(a,b)])

    def test_stack(self):
        self.assertEqual(Machine([1,2,3,4,5,"*","*","*","*"]).run().stack, [120])
        self.assertEqual(Machine([1,2,3,4,5,"-","-","-","-"]).run().stack, [3])
        self.assertEqual(Machine([1,2,3,4,5,"+","+","+","+"]).run().stack, [15])

    def test_arithmetic(self):
        ops = [mul, add]
        for a in range(-10,10):
            for b in range(-10,10):
                for op in ops:
                    self._test_arithmetic(a, b, op)

    def test_optimizer(self):
        self.assertEqual(constant_fold([2,3,"*","."]), [6,"."])
        self.assertEqual(constant_fold([2,2,3,"*","."]), [2,6,"."])
        self.assertEqual(constant_fold([5,2,3,"*","+","."]), [11,"."])
        self.assertEqual(constant_fold([5,2,3,"*","+",4,"*","."]), [44,"."])
        self.assertEqual(constant_fold([2, 3, "+", 5, "*", "println"]),
                [25, "println"])


if __name__ == "__main__":
    unittest.main()
