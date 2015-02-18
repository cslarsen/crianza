"""
A genetic programming simulation that produces programs that double their input
values.
"""

from genetic import *

class DoubleInput(GeneticMachine):
    """A GP machine that produces programs that double their input values.

    E.g., "* 2" or "dup +".
    """
    def __init__(self, code=[]):
        super(DoubleInput, self).__init__(code)
        self._input = 123456

    def new(self, *args, **kw):
        return DoubleInput(*args, **kw)

    #def randomize(self, **kw):
    #    exclude = kw.get("exclude", [])
    #    exclude += ["|", "!", "&", "^", "~", "not", "or", "and", "true", "false"]
    #    kw["exclude"] = exclude
    #    return super(DoubleInput, self).randomize(**kw)

    def setUp(self):
        self._orig = self._code
        self._input = random.randint(0,100)
        self._code = [self._input] + self._code

    def tearDown(self):
        self._code = self._orig

    def score(self):
        top = self.top if vm.isnumber(self.top) else 9999.9

        actual = (top,
                  1000 if self._error else 0,
                  len(self.stack),
                  len(self.return_stack),
                  len(self.code))

        wanted = (self._input*2, # We want to find a way to calculate n*2
                  0, # We don't want errors
                  1, # We the stack to only consist of the answer
                  0, # We want the return stack to be zero
                  2) # We want code to be two instructions

        weights = (0.10, 0.80, 0.02, 0.02, 0.06)
        return 1.0 - weighted_tanimoto(actual, wanted, weights)

    @staticmethod
    def stop(iterations, generation):
        best = sorted(generation, key=lambda m: m.score())
        return average(best, lambda s: s.score()) == 0.0

    def __str__(self):
        return "<DoubleInput %s>" % super(DoubleInput, self).__str__()


if __name__ == "__main__":
    print("Starting ...")
    survivors = iterate(DoubleInput, DoubleInput.stop)

    print("Listing programs from best to worst, unique solutions only.")
    seen = set()
    maxcount = 15
    for n, m in enumerate(survivors):
        if m.code_string not in seen:
            print("%d %s: %s" % (n, m, m.code_string))
            seen.update([m.code_string])
            maxcount -= 1
            if maxcount < 0:
                break
