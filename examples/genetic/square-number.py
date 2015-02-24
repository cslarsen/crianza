"""
A genetic programming simulation that produces programs that double their input
values.
"""

import crianza
import crianza.genetic as gp
import random
import sys


class DoubleInput(gp.GeneticMachine):
    """A GP machine that produces programs that double their input values.

    E.g., "* 2" or "dup +".
    """
    def __init__(self, code=[]):
        super(DoubleInput, self).__init__(code)
        self._input = 123456

    def new(self, *args, **kw):
        return DoubleInput(*args, **kw)

    def randomize(self, **kw):
        ops = map(crianza.instructions.lookup, ["%", "&", "*", "+", "-", "/",
            "<", "<>", "=", ">", "^", "abs", "and", "bool", "drop", "dup",
            "false", "if", "int", "negate", "not", "or", "over", "rot", "swap",
            "true", "|", "~"])
        return super(DoubleInput, self).randomize(number_string_ratio=1.0,
                instruction_ratio=0.75, restrict_to=ops)

    def setUp(self):
        self._orig = self.code
        self._input = random.randint(0,100)
        self.code = [crianza.compiler.make_embedded_push(self._input)] + self.code

    def tearDown(self):
        self.code = self._orig

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
        actual = (self.top if crianza.isnumber(self.top) else 9999.9,
                  1000 if self._error else 0,
                  len(self.stack),
                  len(self.return_stack),
                  len(self.code) if len(self.code)<5 else 999)

        # Return a value from 0.0 (perfect score) to 1.0 (infinitely bad score)
        return 1.0 - gp.weighted_tanimoto(actual, wanted, weights)

    @staticmethod
    def stop(iterations, generation):
        best = sorted(generation, key=lambda m: m.score())
        return gp.average(best, lambda s: s.score()) <= 0.00000012


def splitlines(code, width):
    v = code.split(" ")
    while len(v) > 0:
        line = []
        while len(" ".join(line))<=width and len(v)>0:
            line.append(v.pop(0))
        yield " ".join(line)

if __name__ == "__main__":
    print("Starting ...")

    survivors = gp.iterate(DoubleInput, DoubleInput.stop, machines=100)

    print("\nListing programs from best to worst, unique solutions only.")
    seen = set()
    maxcount = 15
    for n, m in enumerate(survivors):
        if m.code_string not in seen:
            print("%d %s: %s" % (n, m, m.code_string))
            seen.update([m.code_string])
            maxcount -= 1
            if maxcount < 0:
                break

    if len(survivors) == 0:
        sys.exit(0)

    print("\nThe GP found that you can make a square word like so:\n")

    best = survivors[0]
    sys.stdout.write("    : square\n")
    for line in splitlines(best.code_string, width=40):
        sys.stdout.write("        %s" % line)
    sys.stdout.write(" ;\n\n")

    print("Example output:\n")
    correct = 0
    tries = 5
    for n in xrange(tries):
        n = random.randint(0, 1000)
        try:
            r = crianza.execute("%d %s" % (n, best.code_string)).top
            print("    %d square ==> %s" % (n, r))
            if r == n*n:
                correct += 1
        except:
            print("    (genetic program crashed)")
            continue

    print("")
    if correct == tries:
        print("The code SEEMS to be CORRECT.")
    elif correct > 0:
        print("The code is NOT entirely correct, it seems.")
    else:
        print("The code is NOT correct at all!")
