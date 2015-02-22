"""
Contains a collection of useful instructions, or machine primivites.
"""

import errors
import interpreter

def _assert_number(*args):
    for arg in args:
        if not interpreter.isnumber(arg):
            raise errors.MachineError("Not an integer: %s" % str(arg))

def _assert_bool(*args):
    for arg in args:
        if not interpreter.isbool(arg):
            raise errors.MachineError("Not a boolean: %s" % str(arg))

def _assert_binary(*args):
    for arg in args:
        if not interpreter.isbinary(arg):
            raise errors.MachineError("Not boolean or numerical: %s" % str(arg))

def add(vm):
    a = vm.pop()
    b = vm.pop()
    _assert_number(a, b)
    vm.push(a + b)

def sub(vm):
    a = vm.pop()
    b = vm.pop()
    _assert_number(a, b)
    vm.push(b - a)

def call(vm):
    vm.return_stack.push(vm.instruction_pointer)
    jmp(vm)

def return_(vm):
    vm.instruction_pointer = vm.return_stack.pop()

def mul(vm, modulus=None):
    a = vm.pop()
    b = vm.pop()
    _assert_number(a, b)

    if modulus is None:
        vm.push(a * b)
    else:
        vm.push((a * b) % modulus)

def div(vm):
    divisor = vm.pop()
    dividend = vm.pop()
    _assert_number(dividend, divisor)
    if divisor == 0:
        raise errors.MachineError(ZeroDivisionError("Division by zero"))
    vm.push(dividend / divisor)

def mod(vm):
    a = vm.pop()
    b = vm.pop()
    _assert_number(a, b)
    if a == 0:
        raise errors.MachineError(ZeroDivisionError("Division by zero"))
    vm.push(b % a)

def abs_(vm):
    _assert_binary(vm.top)
    vm.push(abs(vm.pop()))

def nop(vm):
    """No operation; do nothing."""
    pass

def exit(vm):
    raise StopIteration

def dup(vm):
    vm.push(vm.top)

def over(vm):
    b = vm.pop()
    a = vm.pop()
    vm.push(a)
    vm.push(b)
    vm.push(a)

def drop(vm):
    vm.pop()

def swap(vm):
    b = vm.pop()
    a = vm.pop()
    vm.push(b)
    vm.push(a)

def rot(vm):
    """Rotate topmost three items once to the left. ( a b c -- b c a )"""
    c = vm.pop()
    b = vm.pop()
    a = vm.pop()
    vm.push(b)
    vm.push(c)
    vm.push(a)

def r_at(vm):
    """Pop top of return stack and push onto data stack."""
    vm.push(vm.data_stack.pop())

def r_gt(vm):
    """Copy top of the return stack and push onto the data stack."""
    vm.push(vm.data_stack.top)

def write(vm, flush=True):
    value = str(vm.pop())
    try:
        if vm.output is not None:
            vm.output.write(value)
            if flush:
                vm.output.flush()
    except IOError:
        raise errors.MachineError(StopIteration)

def at(vm):
    """Pushes previous position to return stack."""
    vm.return_stack.push(vm.instruction_pointer - 1)

def dot(vm, flush=True):
    write(vm, flush=False)
    try:
        if vm.output is not None:
            vm.output.write("\n")
            if flush:
                vm.output.flush()
    except IOError:
        raise errors.MachineError(IOError)

def read(vm):
    line = vm.input.readline().rstrip()
    vm.push(line)

    # To be compatible with the old code that relied on raw_input raising
    # EOFError, we should also do it for a while (later on, we should use
    # another mechanism).
    if line == "":
        raise EOFError()

def cast_int(vm):
    try:
        int(vm.top)
    except ValueError:
        raise errors.MachineError("Cannot be cast to int: '%s'" % str(vm.top))
    else:
        vm.push(int(vm.pop()))

def cast_bool(vm):
    try:
        bool(vm.top)
    except ValueError:
        raise errors.MachineError("Cannot be cast to bool: '%s'" % str(vm.top))
    else:
        vm.push(bool(vm.pop()))

def cast_str(vm):
    try:
        vm.push(str(vm.pop()))
    except ValueError, e:
        raise errors.MachineError(e)

def equal(vm):
    vm.push(vm.pop() == vm.pop())

def not_equal(vm):
    vm.push(vm.pop() != vm.pop())

def less(vm):
    a = vm.pop()
    vm.push(a < vm.pop())

def greater(vm):
    a = vm.pop()
    vm.push(a > vm.pop())

def true_(vm):
    vm.push(True)

def false_(vm):
    vm.push(False)

def if_stmt(vm):
    false_clause = vm.pop()
    true_clause = vm.pop()
    test = vm.pop()

    # False values: False, 0, "", everyting else is true
    if interpreter.isbool(test) and test == False:
        result = False
    elif interpreter.isstring(test) and len(test) == 0:
        result = False
    elif interpreter.isnumber(test) and test == 0:
        result = False
    else:
        result = True

    if result == True:
        vm.push(true_clause)
    else:
        vm.push(false_clause)

def jmp(vm):
    if not (isinstance(vm.top, int) or isinstance(vm.top, long)):
        raise errors.MachineError("Jump address must be an integer: %s" %
                str(vm.top))
    addr = vm.pop()
    if 0 <= addr < len(vm.code):
        vm.instruction_pointer = addr
    else:
        raise errors.MachineError("Jump address out of range: %s" % str(addr))

def dump_stack(vm):
    vm.output.write("Data stack:\n")
    for v in reversed(vm.data_stack._values):
        vm.output.write(" - type %s, value '%s'\n" % (type(v), v))

    vm.output.write("Return stack:\n")
    for v in reversed(vm.return_stack._values):
        vm.output.write(" - address %s\n" % str(v))

    vm.output.flush()

def bitwise_and(vm):
    a = vm.pop()
    b = vm.pop()
    _assert_binary(a, b)
    vm.push(b & a)

def bitwise_or(vm):
    a = vm.pop()
    b = vm.pop()
    _assert_binary(a, b)
    vm.push(b | a)

def bitwise_xor(vm):
    a = vm.pop()
    b = vm.pop()
    _assert_binary(a, b)
    vm.push(b ^ a)

def bitwise_complement(vm):
    a = vm.pop()
    _assert_binary(a)
    vm.push(~a)

def binary_not(vm):
    a = vm.pop()
    _assert_bool(a)
    vm.push(not a)

def binary_and(vm):
    a = vm.pop()
    b = vm.pop()
    _assert_bool(a, b)
    vm.push(b and a)

def binary_or(vm):
    a = vm.pop()
    b = vm.pop()
    _assert_bool(a, b)
    vm.push(b or a)

def negate(vm):
    _assert_number(vm.top)
    vm.push(-vm.pop())

def lookup(instruction, instructions = None):
    """Looks up instruction, which can either be a function or a string.
    If it's a string, returns the corresponding method.
    If it's a function, returns the corresponding name.
    """
    if instructions is None:
        instructions = default_instructions

    if isinstance(instruction, str):
        return instructions[instruction]
    elif hasattr(instruction, "__call__"):
        rev = dict(((v,k) for (k,v) in instructions.items()))
        return rev[instruction]
    else:
        raise errors.MachineError(KeyError("Unknown instruction: %s" %
            str(instruction)))

default_instructions = {
    "%":      mod,
    "&":      bitwise_and,
    "*":      mul,
    "+":      add,
    "-":      sub,
    ".":      dot,
    "/":      div,
    "<":      less,
    "<>":     not_equal,
    "=":      equal,
    ">":      greater,
    "@":      at,
    "^":      bitwise_xor,
    "abs":    abs_,
    "and":    binary_and,
    "bool":   cast_bool,
    "call":   call,
    "drop":   drop,
    "dup":    dup,
    "exit":   exit,
    "false":  false_,
    "if":     if_stmt,
    "int":    cast_int,
    "jmp":    jmp,
    "negate": negate,
    "nop":    nop,
    "not":    binary_not,
    "or":     binary_or,
    "over":   over,
    "read":   read,
    "return": return_,
    "rot":    rot,
    "str":    cast_str,
    "swap":   swap,
    "true":   true_,
    "write":  write,
    "|":      bitwise_or,
    "~":      bitwise_complement,
    #".stack": dump_stack, # Parser doesn't like this
    #"r>":     r_gt, # Parser doesn't like this
    #"r@":     r_at, # Parser doesn't like this
}

