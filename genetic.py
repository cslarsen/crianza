"""
Simple genetic programming using the virtual machine.

TIP: Run with pypy for speed.

See examples in examples-genetic/
"""

import math
import random
import vm

def tanimoto_coefficient(a, b):
    """Measured similarity between two points in a multi-dimensional space.

    Returns:
        1.0 if the two points completely overlap,
        0.0 if the two points are infinitely far apart.
    """
    return sum(map(lambda (x,y): float(x)*float(y), zip(a,b))) / sum([
          -sum(map(lambda (x,y): float(x)*float(y), zip(a,b))),
           sum(map(lambda x: float(x)**2, a)),
           sum(map(lambda x: float(x)**2, b))])

def weighted_tanimoto(a, b, weights):
    """Same as the Tanimoto coefficient, but wit weights for each dimension."""
    weighted = lambda s: map(lambda (x,y): float(x)*float(y), zip(s, weights))
    return tanimoto_coefficient(weighted(a), weighted(b))

def average(sequence, key):
    """Averages a sequence based on a key."""
    return sum(map(key, sequence)) / float(len(sequence))

def weighted_choice(choices):
    # Taken from http://stackoverflow.com/a/3679747/21028
    total = sum(w for c, w in choices)
    r = random.uniform(0, total)
    upto = 0
    for c, w in choices:
        if upto + w > r:
            return c
        upto += w
    assert False, "Shouldn't get here"

def stochastic_choice(machines):
    """Stochastically choose one random machine distributed along their
    scores."""
    r = random.random()
    if r < 0.5:
        return random.choice(machines[:len(machines)/4])
    elif r < 0.75:
        return random.choice(machines[:len(machines)/2])
    else:
        return random.choice(machines)

    #This is better, but waaaay too slow:
    # w = [(1.0 - m.score()) for m in machines]
    # return weighted_choice(zip(machines, w))

def randomize(vm,
        length=(10,10),
        ints=(0,999),
        strs=(1,10),
        instruction_ratio=0.5,
        number_string_ratio=0.8,
        exclude=[".", "exit", "read", "write", "stack"]):

    """Replaces existing code with completely random instructions. Does not
    optimize code after generating it.

    Args:
        length: Tuple of minimum and maximum code lengths. Code length will
        be a random number between these two, inclusive values.

        ints: Integers in the code will be selected at random from this
        inclusive range.

        strs: Inclusive range of the length of strings in the code.

        instruction_ratio: Ratio of instructions to numbers/strings,
        meaning that if this value is 0.5 then there will just as many
        instructions in the code as there are numbers and strings.

        number_string_ratio: Ratio of numbers to strings.

        exclude: Excluded instructions. For genetic programming, one wants
        to avoid the program to hang for user input.  The default value is
        to exclude console i/o and debug instructions.

    Returns:
        The VM.
    """
    vm.code = []
    instructions = dict([i for i in vm.instructions.items() if i[0] not
        in exclude])

    for _ in xrange(random.randint(*length)):
        r = random.random()
        if r <= instruction_ratio:
            # Generate a random instruction
            vm.code.append(random.choice(instructions.keys()))
        elif r <= number_string_ratio:
            # Generate a random number
            vm.code.append(random.randint(*ints))
        else:
            # Generate a random string
            vm.code.append('"%s"' % "".join(chr(random.randint(1,127))
                for n in xrange(0, random.randint(*strs))))
    return vm

def crossover(m, f):
    """Produces an offspring from two Machines, whose code is a
    combination of the two."""
    i = random.randint(0, len(m.code))
    j = random.randint(0, len(f.code))
    return m.code[:i] + f.code[j:]


class GeneticMachine(vm.Machine):
    def __init__(self, code=[]):
        super(GeneticMachine, self).__init__(code)
        self._error = False

    def setUp(self):
        """Called before each invocation of run()."""
        self.reset()
        return self

    def tearDown(self):
        """Called after each invocation of run()."""
        return self

    def new(self, *args, **kw):
        """A virtual constructor.

        Subclasses should override this method to construct correct instances.
        """
        return GeneticMachine(*args, **kw)

    def randomize(self, **kw):
        """Creates a new random code."""
        return randomize(self, **kw)

    def crossover(self, other):
        """Produce offspring from this and another instance."""
        return self.new(crossover(self, other))

    def mutate(self):
        """Mutates code."""
        # Choose a random position
        if len(self.code) == 0:
            return

        index = random.randint(0, len(self.code)-1)
        mutation_type = random.random()

        if mutation_type < 0.5:
            # Change
            self.code[index] = self.new().randomize().code[0]
        elif mutation_type < 0.75:
            # Deletion
            del self.code[index]
        else:
            # Insertion
            self.code.insert(index, self.new().randomize().code[0])

    def run(self, steps=10):
        """Executes up to `steps` instructions."""
        try:
            super(GeneticMachine, self).run(steps)
            self._error = False
        except StopIteration:
            self._error = False
        except Exception:
            self._error = True

    def score(self):
        """Returns a machine's fitness as a number from 0.0 (perfect score) to
        1.0 (worst score).

        This method must be overriden to produce selection pressure, i.e. to
        direct what kind of problem this machine should solve.
        """
        return 1.0 if self._error else 0.0

    def stop(iterations, generation):
        """Conditions for when to stop the simulation."""
        return iterations >= 10000


def iterate(MachineClass, stop_function=lambda iterations: iterations < 10000,
        machines=1000, survival_rate=0.05, mutation_rate=0.075):

    """Creates a bunch of machines, runs them for a number of steps and then
    gives them a fitness score.  The best produce offspring that are passed on
    to the next generation.

    Args:
        setup: Function taking a Machine argument, makes the machine ready
        machine_class: A class that should inherit from Machine and contain the
        following methods:
            setUp(self) [optional]: Run before each new run, should at least
            call self.reset() for each run.

            tearDown(self) [optional]: Run after each run.

            crossover(self, other): Returns a Machine offspring between itself and
            another Machine.

            score(self):  Score the machine. Lower is better. Can return a
            tuple of values used to sort the machines from best to worst in
            fitness.

        stop_function: An optional function that takes the current generation
        number and returns True if the processing should stop.

        machines: The number of machines to create for each generation.

        steps: The number of instructions each machine is allowed to execute in
        each run.

        code_length: Tuple of (minimum code length, maximum code length) for a
        Machine.

        survival_ratio: Ratio of the best Machines which are allowed to produce
        offspring for the next generation.

        mutation_rate: Rate for each machine's chance of being mutated.
    """
    generation = [MachineClass().randomize() for n in xrange(machines)]
    survivors = generation

    try:
        iterations = 0
        while not stop_function(iterations, survivors):
            iterations += 1

            # Run all machines in this generation
            for m in generation:
                m.setUp()
                m.run()
                m.tearDown()

            # Sort machines from best to worst
            generation = sorted(generation, key=lambda m: m.score())

            # Select the best
            survivors = generation[:int(survival_rate * len(generation))]

            # Remove dead ones
            survivors = [s for s in survivors if len(s.code)>0]

            # Create a new generation based on the survivors.
            generation = []
            while len(generation) < machines:
                generation.append(stochastic_choice(survivors).
                        crossover(stochastic_choice(survivors)))

            # Add mutations from time to time
            for m in generation:
                if random.random() > mutation_rate:
                    m.mutate()

            print("gen %d 1-fitness %.12f avg code len %.2f avg stack len %.2f" % (
                iterations,
                average(survivors, lambda m: m.score()),
                average(survivors, lambda m: len(m.code)),
                average(survivors, lambda m: len(m.stack) + len(m.return_stack))))
    except KeyboardInterrupt:
        pass

    return survivors
