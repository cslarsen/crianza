"""
Contains extremely experimental support for compiling to native Python.

Beware that actually running your code as native Python bytecode may segfault
the interpreter!
"""

import byteplay as bp

def mod():
    return [(bp.BINARY_MODULO, None)]

def add():
    return [(bp.BINARY_ADD, None)]

def bitwise_and():
    return [(bp.BINARY_AND, None)]

def mul():
    return [(bp.BINARY_MULTIPLY, None)]

def sub():
    return [(bp.BINARY_SUBTRACT, None)]

def dot():
    # TODO: Use current output stream
    return [(bp.PRINT_ITEM, None)]

def div():
    return [(bp.BINARY_DIVIDE, None)]

def less():
    return [(bp.COMPARE_OP, "<")]

def not_equal():
    return [(bp.COMPARE_OP, "!=")]

def equal():
    return [(bp.COMPARE_OP, "==")]

def greater():
    return [(bp.COMPARE_OP, ">")]

def at():#lineno):
    raise NotImplementedError("at")
    return [(bp.LOAD_CONST, lineno)]

def bitwise_or():
    return [(bp.BINARY_OR, None)]

def bitwise_xor():
    return [(bp.BINARY_XOR, None)]

def __call_function(name):
    return [
        (bp.LOAD_GLOBAL, name), # -- n name
        (bp.ROT_TWO, None),     # -- name n
        (bp.CALL_FUNCTION, None)
    ]

def abs_():
    # We'll just call abs():
    #
    #   >>> import dis
    #   >>> dis.dis(lambda n: abs(n))
    #     1           0 LOAD_GLOBAL              0 (abs)
    #                 3 LOAD_FAST                0 (n)
    #                 6 CALL_FUNCTION            1
    #                 9 RETURN_VALUE             n
    return __call_function("abs")

def binary_and():
    raise NotImplementedError("binary_and")

def cast_bool():
    return __call_function("bool")

def call():
    raise NotImplementedError("call")

def drop():
    return [(bp.POP_TOP, None)]

def dup():
    return [(bp.DUP_TOP, None)]

def exit():
    # TODO: Can be done by raising a specific exception, for instance.
    raise NotImplementedError("exit")

def false_():
    return [(bp.LOAD_CONST, False)]

def cast_float():
    return __call_function("float")

def if_stmt():
    raise NotImplementedError("if")

def cast_int():
    return __call_function("int")

def jmp():
    # TODO: Not so sure about absolute jumps...
    return [(bp.JUMP_ABSOLUTE, None)]

def negate():
    return [(bp.UNARY_NEGATIVE, None)]

def nop():
    return [(bp.NOP, None)]

def binary_not():
    # TODO: Rename our "binary_not" to "unary_not"
    return [(bp.UNARY_NOT, None)]

def binary_or():
    return [(bp.BINARY_OR, None)]

def over():
    # a b -- a b a
    return [
        (bp.DUP_TOPX, 2),   # a b -- a b a b
        (bp.POP_TOP, None), # a b a b -- a b a
    ]

def read():
    raise NotImplementedError("read")

def return_():
    raise NotImplementedError("return")

def rot():
    return [(bp.ROT_THREE, None)]

def cast_str():
    return __call_function("str")

def swap():
    return [(bp.ROT_TWO, None)]

def true_():
    return [(bp.LOAD_CONST, True)]

def write():
    raise NotImplementedError("write")

def bitwise_or():
    return [(bp.BINARY_OR, None)]

def bitwise_complement():
    return [(bp.UNARY_INVERT, None)]

def push(constant):
    return [(bp.LOAD_CONST, constant)]

def to_code(bytecode):
    code = []

    for op in bytecode:
        if isinstance(op, int):
            code += push(op)
        else:
            code += instructions[op]()

    return code

def compile(bytecode, freevars=[], args=(), varargs=False, varkwargs=False,
        newlocals=True, name="", filename="", firstlineno=1, docstring=""):

    code = to_code(bytecode)
    code.append((bp.RETURN_VALUE, None))

    codeobj = bp.Code(code, freevars=[], args=(), varargs=False,
            varkwargs=False, newlocals=True, name="", filename="",
            firstlineno=1, docstring="")

    func = lambda: None
    func.func_code = bp.Code.to_code(codeobj)
    return func

instructions = {
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
    "float":  cast_float,
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
}
