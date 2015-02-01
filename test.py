import operator
import unittest

from vm import Machine

class TestVM(unittest.TestCase):
    def test_initial_conditions(self):
        self.assertEqual(Machine([]).run().stack, [])

    def _test_arithmetic(self, a, b, operator):
        self.assertEqual(Machine([a, b, operator.__name__]).run().stack,
                         [operator(a,b)])

    def test_arithmetic(self):
        self._test_arithmetic(2, 3, operator.add)
        self._test_arithmetic(2, 3, operator.sub)
        self._test_arithmetic(2, 3, operator.mul)
        self._test_arithmetic(2, 3, operator.div)
        self._test_arithmetic(2, 3, operator.mod)


if __name__ == "__main__":
    unittest.main()
