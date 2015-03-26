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
    return [
        (bp.PRINT_ITEM, None),
        (bp.LOAD_CONST, "\n"),
        (bp.PRINT_ITEM, None),
    ]

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

def at(lineno):
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
    return __call_function("abs")

def cast_bool():
    return __call_function("bool")

def call():
    # TODO: Could use JUMP_ABSOLUTE, but we'd have to calculate some offsets
    # due to input arguments.
    raise NotImplementedError("call")

def return_():
    raise NotImplementedError("return")

def drop():
    return [(bp.POP_TOP, None)]

def dup():
    return [(bp.DUP_TOP, None)]

def exit():
    # Return the value on top of the stack to the caller
    return [(bp.RETURN_VALUE)]

def false_():
    return [(bp.LOAD_CONST, False)]

def cast_float():
    return __call_function("float")

def if_stmt(lineno):
    # Stack: false_clause true_clause test
    return [
        (bp.JUMP_IF_FALSE, lineno+3+3), # if false, pop top
        (bp.ROT_TWO, None), # if true, rotate before popping
        (bp.POP_TOP, None),
    ]

def cast_int():
    return __call_function("int")

def jmp():
    # TODO: Not so sure about absolute jumps...
    return [(bp.JUMP_ABSOLUTE, None)]

def negate():
    return [(bp.UNARY_NEGATIVE, None)]

def nop():
    return [(bp.NOP, None)]

def binary_and(lineno):
    # Stack: a b
    return [
        (bp.JUMP_IF_FALSE_OR_POP, lineno+2*3),
        (bp.JUMP_RELATIVE, 3*3),
        (bp.ROT_TWO, None),
        (bp.POP_TOP, None),
    ]

def binary_not():
    # TODO: Rename our "binary_not" to "unary_not"
    # TODO: This is correct, it evaluates "not a"
    return [(bp.UNARY_NOT, None)]

def binary_or():
    # TODO: This is wrong, this is a bitwise op and nor "a or b"
    return [(bp.BINARY_OR, None)]

def over():
    # a b -- a b a
    return [
        (bp.DUP_TOPX, 2),   # a b -- a b a b
        (bp.POP_TOP, None), # a b a b -- a b a
    ]

def read():
    # TODO: Use current input stream
    return [
        (bp.LOAD_GLOBAL, "sys"),
        (bp.LOAD_ATTR, "stdin"),
        (bp.LOAD_ATTR, "readline"),
        (bp.CALL_FUNCTION, None),
        (bp.LOAD_ATTR, "rstrip"),
        (bp.CALL_FUNCTION, None),
    ]

def rot():
    return [(bp.ROT_THREE, None)]

def cast_str():
    return __call_function("str")

def swap():
    return [(bp.ROT_TWO, None)]

def true_():
    return [(bp.LOAD_CONST, True)]

def write():
    # TODO: Use current output stream
    return [
        (bp.PRINT_ITEM, None),
    ]

def bitwise_or():
    return [(bp.BINARY_OR, None)]

def bitwise_complement():
    return [(bp.UNARY_INVERT, None)]

def push(constant):
    return [(bp.LOAD_CONST, constant)]

def to_code(bytecode, firstlineno=1):
    # TODO: Accept completely compiled code (a VM perhaps), with streams etc.
    code = []
    lineno = firstlineno

    for op in bytecode:
        if isinstance(op, int):
            code += push(op)
        elif op == "@":
            code += instructions[op](lineno)
        else:
            code += instructions[op]()
        lineno += 1

    return code

def compile(code, args=0, arglist=(), freevars=[], varargs=False,
        varkwargs=False, newlocals=True, name="", filename="", firstlineno=1,
        docstring=""):

    code = to_code(code, firstlineno)
    code.append((bp.RETURN_VALUE, None))

    if args > 0:
        for n in xrange(args):
            argname = "arg%d" % n
            arglist = arglist + (argname,)
            code = [(bp.LOAD_FAST, argname)] + code

    codeobj = bp.Code(code, freevars=freevars, args=arglist, varargs=varargs,
            varkwargs=varkwargs, newlocals=newlocals, name=name,
            filename=filename, firstlineno=firstlineno, docstring=docstring)

    func = lambda: None
    func.func_code = bp.Code.to_code(codeobj)
    func.__doc__ = docstring # TODO: I thought bp.Code was supposed to do this?
    func.__name__ = name # TODO: Ditto
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

if __name__ == "__main__":
    # A simple test; remove this later.
    import dis
    import random

    mul2 = compile([2,"*"], args=1, name="mul2",
            docstring="Multiplies number with two.")

    for __ in range(10):
        n = random.randint(-100, 100)
        result = "OK" if mul2(n) == n*2 else "FAIL"
        print("%-4s mul2(%d) ==> %d" % (result, n, mul2(n)))
        assert mul2(n) == n*2, "Error in function mul2"

    print("Code for mul2:")
    dis.dis(mul2)
