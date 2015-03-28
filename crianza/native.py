"""
Contains extremely experimental support for compiling to native Python.

Beware that actually running your code as native Python bytecode may segfault
the interpreter!

TODO:
    - Read all jump locations (not entirely possible, actually), convert to
      bp.Label.

    - In the entire language, require that jumps are absolute? if-jumps are OK,
      but they should all be constants (or possible to deduce), so "read int
      jmp" should not be allowable. Or find another way (use structured
      programming for loops, pass on subroutines for call/return to the native
      compiler so it can deduce positions, have compile be able to return these
      positions).

      An alternative would be to do

        labels[lineno] = bp.Label()

      and put a label for each line. That works, but I don't know if the
      byteplay module will optimize away unused jumps for us? (Probably does)
"""

import byteplay as bp
import crianza
import crianza.compiler as cc
import crianza.instructions as cr


def mod(lineno):
    return [(bp.BINARY_MODULO, None)]

def add(lineno):
    return [(bp.BINARY_ADD, None)]

def bitwise_and(lineno):
    return [(bp.BINARY_AND, None)]

def mul(lineno):
    return [(bp.BINARY_MULTIPLY, None)]

def sub(lineno):
    return [(bp.BINARY_SUBTRACT, None)]

def dot(lineno):
    # TODO: Use current output stream
    return [
        (bp.PRINT_ITEM, None),
        (bp.PRINT_NEWLINE, None),
    ]

def div(lineno):
    return [(bp.BINARY_DIVIDE, None)]

def less(lineno):
    return [(bp.COMPARE_OP, "<")]

def not_equal(lineno):
    return [(bp.COMPARE_OP, "!=")]

def equal(lineno):
    return [(bp.COMPARE_OP, "==")]

def greater(lineno):
    return [(bp.COMPARE_OP, ">")]

def at(lineno):
    return [(bp.LOAD_CONST, lineno)]

def bitwise_xor(lineno):
    return [(bp.BINARY_XOR, None)]

def __call_function(name):
    return [
        (bp.LOAD_GLOBAL, name),
        (bp.CALL_FUNCTION, None)
    ]

def abs_(lineno):
    return __call_function("abs")

def cast_bool(lineno):
    return __call_function("bool")

def call(lineno):
    # TODO: Could use JUMP_ABSOLUTE, but we'd have to calculate some offsets
    # due to input arguments.
    raise NotImplementedError("call")

def return_(lineno):
    raise NotImplementedError("return")

def drop(lineno):
    return [(bp.POP_TOP, None)]

def dup(lineno):
    return [(bp.DUP_TOP, None)]

def exit(lineno):
    # Returns None to Python
    return [
        (bp.LOAD_CONST, None),
        (bp.RETURN_VALUE, None),
    ]

def false_(lineno):
    return [(bp.LOAD_CONST, False)]

def cast_float(lineno):
    return __call_function("float")

def if_stmt(lineno):
    # Stack: (p)redicate (c)onsequent (a)lternative
    # Example: "true  'yes' 'no' if" ==> 'yes'
    # Example: "false 'yes' 'no' if" ==> 'no'
    pop = bp.Label()
    return [
        (bp.ROT_THREE, None),        # p c a -- a p c
        (bp.ROT_TWO, None),          # a p c -- a c p
        (bp.POP_JUMP_IF_FALSE, pop),
        (bp.ROT_TWO, None),          #  a c  -- c a
        (pop, None),
        (bp.POP_TOP, None),
    ]

def cast_int(lineno):
    return __call_function("int")

def jmp(lineno):
    # TODO: Make sure that our way of calculating jump locations work
    return [
        (bp.LOAD_CONST, 3),
        (bp.BINARY_FLOOR_DIVIDE, None),
        (bp.JUMP_ABSOLUTE, None),
    ]

def negate(lineno):
    return [(bp.UNARY_NEGATIVE, None)]

def nop(lineno):
    return [(bp.NOP, None)]

def boolean_and(lineno):
    # a b -- (b and a)
    # TODO: Our other lang requires these are booleans
    # TODO: Use JUMP_IF_FALSE_OR_POP and leave either a or b
    label_out = bp.Label()
    return [
        (bp.POP_JUMP_IF_TRUE, label_out), # a b -- a
        (bp.POP_TOP, None),
        (bp.LOAD_CONST, False),
        (label_out, None),
    ]

def boolean_not(lineno):
    return [(bp.UNARY_NOT, None)]

def boolean_or(lineno):
    # TODO: This is wrong. Implement as shown in boolean_and
    return [(bp.BINARY_OR, None)]

def over(lineno):
    # a b -- a b a
    return [
        (bp.DUP_TOPX, 2),   # a b -- a b a b
        (bp.POP_TOP, None), # a b a b -- a b a
    ]

def read(lineno):
    # TODO: Use current input stream
    return [
        (bp.LOAD_GLOBAL, "sys"),
        (bp.LOAD_ATTR, "stdin"),
        (bp.LOAD_ATTR, "readline"),
        (bp.CALL_FUNCTION, None),
        (bp.LOAD_ATTR, "rstrip"),
        (bp.CALL_FUNCTION, None),
    ]

def rot(lineno):
    return [(bp.ROT_THREE, None)]

def cast_str(lineno):
    return __call_function("str")

def swap(lineno):
    return [(bp.ROT_TWO, None)]

def true_(lineno):
    return [(bp.LOAD_CONST, True)]

def write(lineno):
    # TODO: Use current output stream
    return [
        (bp.PRINT_ITEM, None),
    ]

def bitwise_or(lineno):
    return [(bp.BINARY_OR, None)]

def bitwise_complement(lineno):
    return [(bp.UNARY_INVERT, None)]

def push(constant):
    return [(bp.LOAD_CONST, constant)]

def to_code(bytecode, firstlineno=1):
    # TODO: Accept completely compiled code (a VM perhaps), with streams etc.
    code = []
    lineno = firstlineno

    for op in bytecode:
        if cc.is_embedded_push(op):
            code += push(cc.get_embedded_push_value(op))
        else:
            code += opmap[op](lineno)
        lineno += 3

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

    # First of all, push a None value in case we run code like "'hey' .", so
    # that we always have a value to return.
    code = [(bp.LOAD_CONST, None)] + code

    codeobj = bp.Code(code, freevars=freevars, args=arglist, varargs=varargs,
            varkwargs=varkwargs, newlocals=newlocals, name=name,
            filename=filename, firstlineno=firstlineno, docstring=docstring)

    func = lambda: None
    func.func_code = bp.Code.to_code(codeobj)
    func.__doc__ = docstring # TODO: I thought bp.Code was supposed to do this?
    func.__name__ = name # TODO: Ditto
    return func

def xcompile(source_code, args=0, optimize=True):
    """Parses Crianza source code and returns a native Python function.

    Args:
        args: The resulting function's number of input parameters.

    Returns:
        A callable Python function.
    """
    code = crianza.compile(crianza.parse(source_code), optimize=optimize)
    return crianza.native.compile(code, args=args)

def xeval(source, optimize=True):
    """Compiles to native Python bytecode and runs program, returning the
    topmost value on the stack.

    Args:
        optimize: Whether to optimize the code after parsing it.

    Returns:
        None: If the stack is empty
        obj: If the stack contains a single value
        [obj, obj, ...]: If the stack contains many values
    """
    native = xcompile(source, optimize=optimize)
    return native()

opmap = {
    cr.lookup("%"):      mod,
    cr.lookup("&"):      bitwise_and,
    cr.lookup("*"):      mul,
    cr.lookup("+"):      add,
    cr.lookup("-"):      sub,
    cr.lookup("."):      dot,
    cr.lookup("/"):      div,
    cr.lookup("<"):      less,
    cr.lookup("<>"):     not_equal,
    cr.lookup("="):      equal,
    cr.lookup(">"):      greater,
    cr.lookup("@"):      at,
    cr.lookup("^"):      bitwise_xor,
    cr.lookup("abs"):    abs_,
    cr.lookup("and"):    boolean_and,
    cr.lookup("bool"):   cast_bool,
    cr.lookup("call"):   call,
    cr.lookup("drop"):   drop,
    cr.lookup("dup"):    dup,
    cr.lookup("exit"):   exit,
    cr.lookup("false"):  false_,
    cr.lookup("float"):  cast_float,
    cr.lookup("if"):     if_stmt,
    cr.lookup("int"):    cast_int,
    cr.lookup("jmp"):    jmp,
    cr.lookup("negate"): negate,
    cr.lookup("nop"):    nop,
    cr.lookup("not"):    boolean_not,
    cr.lookup("or"):     boolean_or,
    cr.lookup("over"):   over,
    cr.lookup("read"):   read,
    cr.lookup("return"): return_,
    cr.lookup("rot"):    rot,
    cr.lookup("str"):    cast_str,
    cr.lookup("swap"):   swap,
    cr.lookup("true"):   true_,
    cr.lookup("write"):  write,
    cr.lookup("|"):      bitwise_or,
    cr.lookup("~"):      bitwise_complement,
}
