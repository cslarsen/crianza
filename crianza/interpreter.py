from crianza import compiler
from crianza import errors
from crianza import instructions
from crianza import parser
from crianza import stack
import sys

def code_to_string(code):
    s = []
    for op in code:
        if isconstant(op):
            if isstring(op):
                s.append(repr(op))
            else:
                s.append(str(op))
        elif compiler.is_embedded_push(op):
            v = compiler.get_embedded_push_value(op)
            s.append('"%s"' % repr(v)[1:-1] if isinstance(v, str) else repr(v))
        else:
            s.append(str(instructions.lookup(op)))
    return " ".join(s)

def isstring(args, quoted=False):
    """Checks if value is a (quoted) string."""
    isquoted = lambda c: c[0]==c[-1] and c[0] in ['"', "'"]

    if quoted:
        check = lambda c: isinstance(c, str) and isquoted(c)
    else:
        check = lambda c: isinstance(c, str)

    if isinstance(args, list):
        return all(map(check, args))
    else:
        return check(args)

def isnumber(*args):
    """Checks if value is an integer, long integer or float.

    NOTE: Treats booleans as numbers, where True=1 and False=0.
    """
    return all(map(lambda c: isinstance(c, int) or isinstance(c, float), args))

def isbool(*args):
    """Checks if value is boolean."""
    true_or_false = [instructions.lookup(instructions.true_),
                     instructions.lookup(instructions.false_)]
    return all(map(lambda c: isinstance(c, bool) or c in true_or_false, args))

def isbinary(*args):
    """Checks if value can be part of binary/bitwise operations."""
    return all(map(lambda c: isnumber(c) or isbool(c), args))

def isconstant(args, quoted=False):
    """Checks if value is a boolean, number or string."""
    check = lambda c: isbool(c) or isnumber(c) or isstring(c, quoted)
    if isinstance(args, list):
        return all(map(check, args))
    else:
        return check(args)

def execute(source, optimize=True, output=sys.stdout, input=sys.stdin, steps=-1):
    """Compiles and runs program, returning the machine used to execute the
    code.

    Args:
        optimize: Whether to optimize the code after parsing it.
        output: Stream which program can write output to.
        input: Stream which program can read input from.
        steps: An optional maximum number of instructions to execute on the
            virtual machine.  Set to -1 for no limit.

    Returns:
        A Machine instance.
    """
    code = compiler.compile(parser.parse(source), optimize=optimize)
    machine = Machine(code, output=output, input=input)
    return machine.run(steps)

def eval(source, optimize=True, output=sys.stdout, input=sys.stdin, steps=-1):
    """Compiles and runs program, returning the values on the stack.

    To return the machine instead, see execute().

    Args:
        optimize: Whether to optimize the code after parsing it.
        output: Stream which program can write output to.
        input: Stream which program can read input from.
        steps: An optional maximum number of instructions to execute on the
            virtual machine.  Set to -1 for no limit.

    Returns:
        None: If the stack is empty
        obj: If the stack contains a single value
        [obj, obj, ...]: If the stack contains many values
    """
    machine = execute(source, optimize=optimize, output=output, input=input,
            steps=steps)
    ds = machine.stack

    if len(ds) == 0:
        return None
    elif len(ds) == 1:
        return ds[-1]
    else:
        return ds


class Machine(object):
    """A virtual machine with code, a data stack and an instruction stack."""

    def __init__(self, code, output=sys.stdout, input=sys.stdin):
        """
        Args:
            code: The code to run.
            output: Output stream that the machine's code can write to.
            input: Input stream that the machine's code can read from.
            optimize: If True, optimize the given code.
        """
        self.reset()
        self.code = code
        self.output = output
        self.input = input
        self.instructions = instructions.default_instructions

    def lookup(self, instruction):
        """Looks up name-to-function or function-to-name."""
        return instructions.lookup(instruction, self.instructions)

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
        return code_to_string(self.code)

    def pop(self):
        """Pops the data stack, returning the value."""
        try:
            return self.data_stack.pop()
        except errors.MachineError as e:
            raise errors.MachineError("%s: At index %d in code: %s" %
                    (e, self.instruction_pointer, self.code_string))

    def push(self, value):
        """Pushes a value on the data stack."""
        self.data_stack.push(value)

    @property
    def top(self):
        """Returns the top of the data stack."""
        return self.data_stack.top

    def step(self):
        """Executes one instruction and stops."""
        op = self.code[self.instruction_pointer]
        self.instruction_pointer += 1
        op(self)

    def run(self, steps=None):
        """Run threaded code in machine.

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
