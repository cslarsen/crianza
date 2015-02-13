"""
Very simple genetic programming example using the virtual machine.

TODO:
- Crossover should allow this:
        parent1:    .........
        parent2:    ---------
        result:     ..----...
        instead of: ....-----
- Refactor the main code, make it modular (should be completely controllable
  from the outside)
"""

import random
import vm

class GeneticMachine(vm.Machine):
    """A really simple machine for genetic programming."""

    def __init__(self, code=[]):
        vm.Machine.__init__(self, code)

    def randomize(self, min_code_length=10, max_code_length=10, maxabsint=9999,
            maxstrlen=10, excluded_ops=[".", "exit", "read", "write", "stack"]):
        """Creates random instructions."""
        self.code = []

        # Remove some commands we don't wand the machine to include
        ops = self.dispatch_map
        for op in excluded_ops:
            del ops[op]

        length = random.randint(min_code_length, max_code_length)

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

# TODO:
def main(num_machines=1000, generations=100000, steps=20, max_codelen=10,
        keep_top=100, mutation_rate=0.05):

    """Attemptes to create a program that puts the number 123 on the top of the
    stack.
    """

    print("Using GP to create a program that puts 123 on the ToS.")

    def fitfunc(vm):
        slen = len(vm.stack)
        default = 9999.9, slen, len(vm.code)

        # Machines with no code should not live to next generation
        if len(vm.stack) > 0 and len(vm.code) > 0:
            tos = vm.top
            if isinstance(tos, int):
                distance = abs(123.0 - tos)/123.0
                return distance, slen, len(vm.code)
        return default

    machines = [GeneticMachine().randomize(1, max_codelen) for n in xrange(0,num_machines)]

    try:
        for no in xrange(0, generations):
            # Run all machines and collect results (top of stack)
            results = [(m.reset().run_limited(steps), i) for (i,m) in enumerate(machines)]

            # Calculate their fitness score, sort by fitness, code length
            orig = machines
            fitness = sorted(map(lambda (r,i): (fitfunc(orig[i]),i), results))

            # Select the best
            best = [machines[i] for (r,i) in fitness[:keep_top]]

            # Interbreed them (TODO: choose stochastically with result as
            # weight)
            machines = []
            while len(machines) < num_machines:
                try:
                    # TODO: Could make sure that m!=f here
                    m = random.choice(best)
                    f = random.choice(best)
                    machines.append(m.crossover(f))
                except IndexError:
                    break

            # Adds mutations from time to time
            for m in machines:
                if random.random() < mutation_rate:
                    # Mutation consists of changing, inserting or deleting an
                    # instruction
                    kind = random.random()
                    i = random.randint(0, -1+len(m.code))
                    op = GeneticMachine([]).randomize().code[0]
                    if kind <= 0.5:
                        # change
                        m.code[i] = op
                    elif kind <= 0.75:
                        # deletion
                        del m.code[i]
                    else:
                        # insertion
                        m.code.insert(i, op)

            # Display results
            chosen = [(orig[i], result) for result, i in fitness[:keep_top]]
            avg = sum(res for (m,(res,slen,codelen)) in chosen)/float(len(chosen))
            avglen = sum(codelen for (m,(res,slen,codelen)) in chosen)/float(len(chosen))
            slen = sum(slen for (m,(res,slen,codelen)) in chosen)/float(len(chosen))
            print("Gen %d: machines=%d avg_fitness=%.7f avg_slen=%.7f avg_codelen=%.7f" %
                    (no, len(orig), avg, slen, avglen))

            if avg == 0.0 and avglen < 2:
                print("Stopping because avg==0 and avglen<2.")
                break
    except KeyboardInterrupt:
        pass

    print("Best 10:")
    for m, (result, slen, codelen) in chosen[0:10]:
        print("fitness=%f tos=%s slen=%d len=%d code: %s" % (result, m.top,
            slen, len(m.code), m.code_string))

if __name__ == "__main__":
    main()
