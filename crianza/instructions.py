from errors import MachineError

def lookup(instruction):
    """Looks up instruction, which can either be a function or a string.
    If it's a string, returns the corresponding method.
    If it's a function, returns the corresponding name.
    """
    return Instruction.lookup(instruction)


class Instruction(object):
    """A collection of useful instructions default to each newly created
    Machine."""

    @staticmethod
    def _assert_number(*args):
        for arg in args:
            if not isnumber(arg):
                raise MachineError("Not an integer: %s" % str(arg))

    @staticmethod
    def _assert_bool(*args):
        for arg in args:
            if not isbool(arg):
                raise MachineError("Not a boolean: %s" % str(arg))

    @staticmethod
    def _assert_binary(*args):
        for arg in args:
            if not isbinary(arg):
                raise MachineError("Not boolean or numerical: %s" % str(arg))

    @staticmethod
    def add(vm):
        a = vm.pop()
        b = vm.pop()
        Instruction._assert_number(a, b)
        vm.push(a + b)

    @staticmethod
    def sub(vm):
        a = vm.pop()
        b = vm.pop()
        Instruction._assert_number(a, b)
        vm.push(b - a)

    @staticmethod
    def call(vm):
        vm.return_stack.push(vm.instruction_pointer)
        Instruction.jmp(vm)

    @staticmethod
    def return_(vm):
        vm.instruction_pointer = vm.return_stack.pop()

    @staticmethod
    def mul(vm, modulus=None):
        a = vm.pop()
        b = vm.pop()
        Instruction._assert_number(a, b)

        if modulus is None:
            vm.push(a * b)
        else:
            vm.push((a * b) % modulus)

    @staticmethod
    def div(vm):
        divisor = vm.pop()
        dividend = vm.pop()
        Instruction._assert_number(dividend, divisor)
        if divisor == 0:
            raise MachineError(ZeroDivisionError("Division by zero"))
        vm.push(dividend / divisor)

    @staticmethod
    def mod(vm):
        a = vm.pop()
        b = vm.pop()
        Instruction._assert_number(a, b)
        if a == 0:
            raise MachineError(ZeroDivisionError("Division by zero"))
        vm.push(b % a)

    @staticmethod
    def abs_(vm):
        Instruction._assert_binary(vm.top)
        vm.push(abs(vm.pop()))

    @staticmethod
    def nop(vm):
        """No operation; do nothing."""
        pass

    @staticmethod
    def exit(vm):
        raise StopIteration

    @staticmethod
    def dup(vm):
        vm.push(vm.top)

    @staticmethod
    def over(vm):
        b = vm.pop()
        a = vm.pop()
        vm.push(a)
        vm.push(b)
        vm.push(a)

    @staticmethod
    def drop(vm):
        vm.pop()

    @staticmethod
    def swap(vm):
        b = vm.pop()
        a = vm.pop()
        vm.push(b)
        vm.push(a)

    @staticmethod
    def rot(vm):
        """Rotate topmost three items once to the left. ( a b c -- b c a )"""
        c = vm.pop()
        b = vm.pop()
        a = vm.pop()
        vm.push(b)
        vm.push(c)
        vm.push(a)

    @staticmethod
    def r_at(vm):
        """Pop top of return stack and push onto data stack."""
        vm.push(vm.data_stack.pop())

    @staticmethod
    def r_gt(vm):
        """Copy top of the return stack and push onto the data stack."""
        vm.push(vm.data_stack.top)

    @staticmethod
    def write(vm, flush=True):
        value = str(vm.pop())
        try:
            if vm.output is not None:
                vm.output.write(value)
                if flush:
                    vm.output.flush()
        except IOError:
            raise MachineError(StopIteration)

    @staticmethod
    def at(vm):
        """Pushes previous position to return stack."""
        vm.return_stack.push(vm.instruction_pointer - 1)

    @staticmethod
    def dot(vm, flush=True):
        Instruction.write(vm, flush=False)
        try:
            if vm.output is not None:
                vm.output.write("\n")
                if flush:
                    vm.output.flush()
        except IOError:
            raise MachineError(IOError)

    @staticmethod
    def read(vm):
        vm.push(raw_input())

    @staticmethod
    def cast_int(vm):
        try:
            int(vm.top)
        except ValueError:
            raise MachineError("Cannot be cast to int: %s" % str(vm.top))
        else:
            vm.push(int(vm.pop()))

    @staticmethod
    def cast_bool(vm):
        try:
            bool(vm.top)
        except ValueError:
            raise MachineError("Cannot be cast to bool: %s" % str(vm.top))
        else:
            vm.push(bool(vm.pop()))

    @staticmethod
    def cast_str(vm):
        try:
            vm.push(str(vm.pop()))
        except ValueError, e:
            raise MachineError(e)

    @staticmethod
    def equal(vm):
        vm.push(vm.pop() == vm.pop())

    @staticmethod
    def not_equal(vm):
        vm.push(vm.pop() != vm.pop())

    @staticmethod
    def less(vm):
        a = vm.pop()
        vm.push(a < vm.pop())

    @staticmethod
    def greater(vm):
        a = vm.pop()
        vm.push(a > vm.pop())

    @staticmethod
    def true_(vm):
        vm.push(True)

    @staticmethod
    def false_(vm):
        vm.push(False)

    @staticmethod
    def if_stmt(vm):
        false_clause = vm.pop()
        true_clause = vm.pop()
        test = vm.pop()

        # False values: False, 0, "", everyting else is true
        if isbool(test) and test == False:
            result = False
        elif isstring(test) and len(test) == 0:
            result = False
        elif isnumber(test) and test == 0:
            result = False
        else:
            result = True

        if result == True:
            vm.push(true_clause)
        else:
            vm.push(false_clause)

    @staticmethod
    def jmp(vm):
        if not (isinstance(vm.top, int) or isinstance(vm.top, long)):
            raise MachineError("Jump address must be an integer: %s" %
                    str(vm.top))
        addr = vm.pop()
        if 0 <= addr < len(vm.code):
            vm.instruction_pointer = addr
        else:
            raise MachineError("Jump address out of range: %s" % str(addr))

    @staticmethod
    def dump_stack(vm):
        vm.output.write("Data stack:\n")
        for v in reversed(vm.data_stack._values):
            vm.output.write(" - type %s, value '%s'\n" % (type(v), v))

        vm.output.write("Return stack:\n")
        for v in reversed(vm.return_stack._values):
            vm.output.write(" - address %s\n" % str(v))

        vm.output.flush()

    @staticmethod
    def bitwise_and(vm):
        a = vm.pop()
        b = vm.pop()
        Instruction._assert_binary(a, b)
        vm.push(b & a)

    @staticmethod
    def bitwise_or(vm):
        a = vm.pop()
        b = vm.pop()
        Instruction._assert_binary(a, b)
        vm.push(b | a)

    @staticmethod
    def bitwise_xor(vm):
        a = vm.pop()
        b = vm.pop()
        Instruction._assert_binary(a, b)
        vm.push(b ^ a)

    @staticmethod
    def bitwise_complement(vm):
        a = vm.pop()
        Instruction._assert_binary(a)
        vm.push(~a)

    @staticmethod
    def binary_not(vm):
        a = vm.pop()
        Instruction._assert_bool(a)
        vm.push(not a)

    @staticmethod
    def binary_and(vm):
        a = vm.pop()
        b = vm.pop()
        Instruction._assert_bool(a, b)
        vm.push(b and a)

    @staticmethod
    def binary_or(vm):
        a = vm.pop()
        b = vm.pop()
        Instruction._assert_bool(a, b)
        vm.push(b or a)

    @staticmethod
    def negate(vm):
        Instruction._assert_number(vm.top)
        vm.push(-vm.pop())

    @staticmethod
    def lookup(instruction, instructions = None):
        """Looks up instruction, which can either be a function or a string.
        If it's a string, returns the corresponding method.
        If it's a function, returns the corresponding name.
        """
        if instructions is None:
            instructions = Instruction.default_instructions

        if isinstance(instruction, str):
            return instructions[instruction]
        elif hasattr(instruction, "__call__"):
            rev = dict(((v,k) for (k,v) in instructions.items()))
            return rev[instruction]
        else:
            raise MachineError(KeyError("Unknown instruction: %s" %
                str(instruction)))

Instruction.default_instructions = {
    "%":      Instruction.mod,
    "&":      Instruction.bitwise_and,
    "*":      Instruction.mul,
    "+":      Instruction.add,
    "-":      Instruction.sub,
    ".":      Instruction.dot,
    "/":      Instruction.div,
    "<":      Instruction.less,
    "<>":     Instruction.not_equal,
    "=":      Instruction.equal,
    ">":      Instruction.greater,
    "@":      Instruction.at,
    "^":      Instruction.bitwise_xor,
    "abs":    Instruction.abs_,
    "and":    Instruction.binary_and,
    "bool":   Instruction.cast_bool,
    "call":   Instruction.call,
    "drop":   Instruction.drop,
    "dup":    Instruction.dup,
    "exit":   Instruction.exit,
    "false":  Instruction.false_,
    "if":     Instruction.if_stmt,
    "int":    Instruction.cast_int,
    "jmp":    Instruction.jmp,
    "negate": Instruction.negate,
    "nop":    Instruction.nop,
    "not":    Instruction.binary_not,
    "or":     Instruction.binary_or,
    "over":   Instruction.over,
    "read":   Instruction.read,
    "return": Instruction.return_,
    "rot":    Instruction.rot,
    "str":    Instruction.cast_str,
    "swap":   Instruction.swap,
    "true":   Instruction.true_,
    "write":  Instruction.write,
    "|":      Instruction.bitwise_or,
    "~":      Instruction.bitwise_complement,
#    ".stack": Instruction.dump_stack, # Parser doesn't like this
#    "r>":     Instruction.r_gt, # Parser doesn't like this
#    "r@":     Instruction.r_at, # Parser doesn't like this
}


from vm import (
    isbinary,
    isbool,
    isnumber,
    isstring
)


