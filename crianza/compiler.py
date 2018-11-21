from crianza.errors import CompileError
from crianza.interpreter import Machine, isconstant, isstring, isbool, isnumber
from crianza import instructions
from crianza import optimizer

EMBEDDED_PUSH_TAG = "embedded_push"

def make_embedded_push(value):
    """Returns a closure that pushed the given value onto a Machine's stack.

    We use this to embed stack pushes in the VM code, so that the interpreter
    can assume that all instructions are callable Python functions. This makes
    dispatching much faster than checking if an instruction is a constant
    (number, string, etc) or a Python function.
    """
    push = lambda vm: vm.push(value)
    push.tag = EMBEDDED_PUSH_TAG
    return push

def is_embedded_push(obj):
    """Checks if an instruction object is an embedded push."""
    return callable(obj) and hasattr(obj, "tag") and obj.tag==EMBEDDED_PUSH_TAG

def get_embedded_push_value(obj):
    """Extracts the embedded push value."""
    assert(is_embedded_push(obj))
    assert(len(obj.__closure__) == 1)
    return obj.__closure__[0].cell_contents

def check(code):
    """Checks code for obvious errors."""
    def safe_lookup(op):
        try:
            return instructions.lookup(op)
        except Exception:
            return op

    for i, a in enumerate(code):
        b = code[i+1] if i+1 < len(code) else None

        # Does instruction exist?
        if not isconstant(a):
            try:
                instructions.lookup(a)
            except KeyError as err:
                # Skip embedded push closures
                if not (len(err.args)==1 and is_embedded_push(err.args[0])):
                    raise CompileError("Instruction at index %d is unknown: %s"
                            % (i, a))

        # Invalid: <str> int
        if isstring(a) and safe_lookup(b) == instructions.cast_int:
            raise CompileError(
                "Cannot convert string to integer (index %d): %s %s" % (i, a,
                    b))

        # Invalid: <int> <binary op>
        boolean_ops = [instructions.boolean_not,
                      instructions.boolean_or,
                      instructions.boolean_and]

        if not isbool(a) and safe_lookup(b) in boolean_ops:
            raise CompileError(
                "Can only use binary operators on booleans (index %d): %s %s" %
                    (i, a, b))
    return code

def compile(code, silent=True, ignore_errors=False, optimize=True):
    """Compiles subroutine-forms into a complete working code.

    A program such as:

        : sub1 <sub1 code ...> ;
        : sub2 <sub2 code ...> ;
        sub1 foo sub2 bar

    is compiled into:

        <sub1 address> call
        foo
        <sub2 address> call
        exit
        <sub1 code ...> return
        <sub2 code ...> return

    Optimizations are first done on subroutine bodies, then on the main loop
    and finally, symbols are resolved (i.e., placeholders for subroutine
    addresses are replaced with actual addresses).

    Args:
        silent: If set to False, will print optimization messages.

        ignore_errors: Only applies to the optimization engine, if set to False
            it will not raise any exceptions. The actual compilatio will still
            raise errors.

        optimize: Flag to control whether to optimize code.

    Raises:
        CompilationError - Raised if invalid code is detected.

    Returns:
        An array of code that can be run by a Machine. Typically, you want to
        pass this to a Machine without doing optimizations.

    Usage:
        source = parse("<source code>")
        code = compile(source)
        machine = Machine(code, optimize=False)
        machine.run()
    """
    assert(isinstance(code, list))

    output = []
    subroutine = {}
    builtins = Machine([]).instructions

    # Gather up subroutines
    try:
        it = code.__iter__()
        while True:
            word = next(it)
            if word == ":":
                name = next(it)
                if name in builtins:
                    raise CompileError("Cannot shadow internal word definition '%s'." % name)
                if name in [":", ";"]:
                    raise CompileError("Invalid word name '%s'." % name)
                subroutine[name] = []
                while True:
                    op = next(it)
                    if op == ";":
                        subroutine[name].append(instructions.lookup(instructions.return_))
                        break
                    else:
                        subroutine[name].append(op)
            else:
                output.append(word)
    except StopIteration:
        pass

    # Expand all subroutine words to ["<name>", "call"]
    for name, code in subroutine.items():
        # For subroutines
        xcode = []
        for op in code:
            xcode.append(op)
            if op in subroutine:
                xcode.append(instructions.lookup(instructions.call))
        subroutine[name] = xcode

    # Compile main code (code outside of subroutines)
    xcode = []
    for op in output:
        xcode.append(op)
        if op in subroutine:
            xcode.append(instructions.lookup(instructions.call))

    # Because main code comes before subroutines, we need to explicitly add an
    # exit instruction
    output = xcode
    if len(subroutine) > 0:
        output += [instructions.lookup(instructions.exit)]

    # Optimize main code
    if optimize:
        output = optimizer.optimized(output, silent=silent, ignore_errors=False)

    # Add subroutines to output, track their locations
    location = {}
    for name, code in subroutine.items():
        location[name] = len(output)
        if optimize:
            output += optimizer.optimized(code, silent=silent, ignore_errors=False)
        else:
            output += code

    # Resolve all subroutine references
    for i, op in enumerate(output):
        if op in location:
            output[i] = location[op]

    output = native_types(output)
    if not ignore_errors:
        check(output)
    return output

def to_bool(instr):
    if isinstance(instr, bool):
        return instr
    elif instr == instructions.lookup(instructions.true_):
        return True
    elif instr == instructions.lookup(instructions.false_):
        return False
    else:
        raise CompileError("Unknown instruction: %s" % instr)

def native_types(code):
    """Convert code elements from strings to native Python types."""
    out = []
    for c in code:
        if isconstant(c, quoted=True):
            if isstring(c, quoted=True):
                v = c[1:-1]
            elif isbool(c):
                v = to_bool(c)
            elif isnumber(c):
                v = c
            else:
                raise CompileError("Unknown type %s: %s" % (type(c).__name__, c))

            # Instead of pushing constants in the code, we always push callable
            # Python functions, for fast dispatching:
            out.append(make_embedded_push(v))
        else:
            try:
                out.append(instructions.lookup(c))
            except KeyError:
                raise CompileError("Unknown word '%s'" % c)
    return out
