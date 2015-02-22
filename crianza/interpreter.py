import instructions
import optimizer
import stack
import sys

def isstring(*args):
    """Checks if value is a quoted string."""
    return all(map(lambda c: isinstance(c, str) and c[0]==c[-1]=='"', args))

def isnumber(*args):
    """Checks if value is an integer, long integer or float.

    NOTE: Treats booleans as numbers, where True=1 and False=0.
    """
    return all(map(lambda c: isinstance(c, int) or isinstance(c, long) or
        isinstance(c, float), args))

def isbool(*args):
    """Checks if value is boolean."""
    true_or_false = [instructions.lookup(instructions.true_),
                     instructions.lookup(instructions.false_)]
    return all(map(lambda c: isinstance(c, bool) or c in true_or_false, args))

def isbinary(*args):
    """Checks if value can be part of binary/bitwise operations."""
    return all(map(lambda c: isnumber(c) or isbool(c), args))

def isconstant(*args):
    """Checks if value is a boolean, number or string."""
    return all(map(lambda c: isbool(c) or isnumber(c) or isstring(c), args))

def execute(source, optimize=True, output=sys.stdout, steps=-1):
    """Compiles and runs program, returning the machine used to execute the
    code.

    Args:
        optimize: Whether to optimize the code after parsing it.
        output: Stream which program can write output to.
        steps: An optional maximum number of instructions to execute on the
            virtual machine.  Set to -1 for no limit.

    Returns:
        A Machine instance.
    """
    code = compile(parse(source), optimize=optimize)
    machine = Machine(code, optimize=False, output=output)
    return machine.run(steps)

def eval(source, optimize=True, output=sys.stdout, steps=-1):
    """Compiles and runs program, returning the values on the stack.

    To return the machine instead, see execute().

    Args:
        optimize: Whether to optimize the code after parsing it.
        output: Stream which program can write output to.
        steps: An optional maximum number of instructions to execute on the
            virtual machine.  Set to -1 for no limit.

    Returns:
        None: If the stack is empty
        obj: If the stack contains a single value
        [obj, obj, ...]: If the stack contains many values
    """
    machine = execute(source, optimize=optimize, output=output, steps=steps)
    stack = machine.stack

    if len(stack) == 0:
        return None
    elif len(stack) == 1:
        return stack[-1]
    else:
        return stack


class Machine(object):
    """A virtual machine with code, a data stack and an instruction stack."""

    def __init__(self, code, output=sys.stdout, optimize=True):
        """
        Args:
            code: The code to run.
            output: Output stream that the machine's code can write to.
            optimize: If True, optimize the given code.
        """
        self.reset()
        self._code = code if optimize == False else optimizer.optimized(code)
        self._optimize = optimize
        self.output = output
        self.instructions = instructions.default_instructions

    def lookup(self, instruction):
        """Looks up name-to-function or function-to-name."""
        return instructions.lookup(instruction, self.instructions)

    @property
    def code(self):
        """The machine's code."""
        return self._code

    @code.setter
    def code(self, value):
        self._code = value if not self._optimize else optimizer.optimized(value)

    @property
    def stack(self):
        """Returns the data (operand) stack values."""
        return self.data_stack._values

    def reset(self):
        """Reset stacks and instruction pointer."""
        self.data_stack = stack.Stack()
        self.return_stack = stack.Stack()
        self.instruction_pointer = 0
        return self

    def __repr__(self):
        return "<Machine: ip=%d |ds|=%d |rs|=%d top=%s>" % (self.instruction_pointer,
                len(self.data_stack), len(self.return_stack), str(self.top))

    def __str__(self):
        return self.__repr__()

    @property
    def code_string(self):
        """Returns code as a parseable string."""
        s = []
        for op in self.code:
            if isstring(op):
                s.append(repr(op)[1:-1])
            else:
                s.append(str(op))
        return " ".join(s)

    def pop(self):
        """Pops the data stack, returning the value."""
        return self.data_stack.pop()

    def push(self, value):
        """Pushes a value on the data stack."""
        self.data_stack.push(value)

    @property
    def top(self):
        """Returns the top of the data stack."""
        return self.data_stack.top

    def step(self):
        """Executes one instruction and stops."""
        instruction = self.code[self.instruction_pointer]
        self.instruction_pointer += 1
        self.dispatch(instruction)

    def run(self, steps=None):
        """Run machine, dispatching instructions.

        Args:
            steps: If specified, run that many number of instructions before
            stopping.
        """
        try:
            while self.instruction_pointer < len(self.code):
                self.step()

                if steps is not None:
                    steps -= 1
                    if steps == 0:
                        break
        except StopIteration:
            pass
        except EOFError:
            pass
        return self

    def dispatch(self, op):
        """Executes one operation by dispatching to a function."""
        if op in self.instructions:
            instruction = self.instructions[op]
            instruction(self)
        elif isnumber(op):
            # Push numbers on data stack
            self.push(op)
        elif isstring(op):
            # Push unquoted string on data stack
            self.push(op[1:-1])
        else:
            raise MachineError("Unknown instruction '%s' at index %d" %
                    (op, self.instruction_pointer))
