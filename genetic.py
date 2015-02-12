"""
Very simple genetic programming example using the virtual machine.

TODO:
- Crossover should allow this:
        parent1:    .........
        parent2:    ---------
        result:     ..----...
        instead of: ....-----
"""

import random
import vm

class GeneticMachine(vm.Machine):
    """A really simple machine for genetic programming."""

    def __init__(self, code=[]):
        vm.Machine.__init__(self, code)

    def randomize(self, length=10, maxabsint=9999, maxstrlen=10):
        """Creates random instructions."""
        self.code = []

        ops = self.dispatch_map
        del ops["."]
        del ops["exit"]
        del ops["read"]
        del ops["write"]
        del ops["stack"]

        for _ in xrange(length):
            optype = random.randint(0,100)
            if optype <= 50:
                self.code.append(random.choice(ops.keys()))
            elif optype <= 90:
                #self.code.append(random.randint(-maxabsint, maxabsint))
                self.code.append(random.randint(0, maxabsint))
            else:
                length = random.randint(1, maxstrlen)
                string = "".join(chr(random.randint(1,127)) for n in xrange(0,
                    length))
                self.code.append('"%s"' % string)
        return self

    def crossover(self, other):
        minlen = min(len(self.code), len(other.code))
        point = random.randint(0, minlen)
        code = self.code[:point] + other.code[point:]
        return GeneticMachine(code)

    def run_limited(self, steps=100, propagate_errors=False):
        for n in xrange(0,steps):
            try:
                self.step()
            except StopIteration:
                break
            except Exception:
                if propagate_errors:
                    raise

                # NOTE: if you want programs that may raise exceptions, but
                # otherwise produce a valid value on the top of the stack, you
                # "break" here.
                #
                # Otherwise, if you want valid programs, "return None" here.
                # Returning None gives no score for incorrect programs, but is
                # much slower to converge.
                return None

        if len(self.stack) > 0:
            return self.stack[-1]
        else:
            return None

def main(num_machines=1000, generations=100000, steps=20, codelen=10,
        keep_top=100, mutation_rate=0.05):

    """Attemptes to create a program that puts the number 123 on the top of the
    stack.
    """

    print("Using GP to create a program that puts 123 on the ToS.")

    def fitfunc(res):
        if isinstance(res, int):
            return abs(123.0 - res)/123.0
        else:
            return 9999.9

    machines = [GeneticMachine().randomize(codelen) for n in xrange(0,num_machines)]

    try:
        for no in xrange(0, generations):
            # Run all machines and collect results (top of stack)
            results = [(m.reset().run_limited(steps), i) for (i,m) in enumerate(machines)]

            # Calculate their fitness score
            orig = machines
            fitness = sorted(map(lambda (r,i): (fitfunc(r),i), results))

            # Select the best
            best = [machines[i] for (r,i) in fitness[:keep_top]]

            # Interbreed them (TODO: choose stochastically with result as
            # weight)
            machines = []
            while len(machines) < num_machines:
                try:
                    m = random.choice(best)
                    f = random.choice(best)
                    machines.append(m.crossover(f))
                except IndexError:
                    break

            # Adds mutations from time to time
            for m in machines:
                if random.random() < mutation_rate:
                    i = random.randint(0, -1+len(m.code))
                    m.code[i] = GeneticMachine([]).randomize().code[0]

            # Display results
            chosen = [(orig[i], result) for result, i in fitness[:keep_top]]
            avg = sum(res for m,res in chosen)/len(chosen)
            print("Gen %d: avg %s" % (no, avg))
    except KeyboardInterrupt:
        pass

    print("Best 10:")
    for m, result in chosen[0:10]:
        print("fitness=%f tos=%s code: %s" % (result, m.top, m.code_string))

if __name__ == "__main__":
    main()
