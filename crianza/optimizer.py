from errors import CompileError
from instructions import lookup, Instruction
import vm


def optimized(code, silent=True, ignore_errors=True):
    """Performs optimizations on already parsed code."""
    return constant_fold(code, silent=silent, ignore_errors=ignore_errors)

def constant_fold(code, silent=True, ignore_errors=True):
    """Constant-folds simple expressions like 2 3 + to 5.

    Args:
        silent: Flag that controls whether to print optimizations made.
        ignore_errors: Whether to raise exceptions on found errors.
    """

    # Loop until we haven't done any optimizations.  E.g., "2 3 + 5 *" will be
    # optimized to "5 5 *" and in the next iteration to 25.

    arithmetic = [
        lookup(Instruction.add),
        lookup(Instruction.bitwise_and),
        lookup(Instruction.bitwise_or),
        lookup(Instruction.bitwise_xor),
        lookup(Instruction.div),
        lookup(Instruction.equal),
        lookup(Instruction.greater),
        lookup(Instruction.less),
        lookup(Instruction.mod),
        lookup(Instruction.mul),
        lookup(Instruction.sub),
    ]

    divzero = [
        lookup(Instruction.div),
        lookup(Instruction.mod),
    ]

    keep_running = True
    while keep_running:
        keep_running = False
        # Find two consecutive numbes and an arithmetic operator
        for i, a in enumerate(code):
            b = code[i+1] if i+1 < len(code) else None
            c = code[i+2] if i+2 < len(code) else None

            # Constant fold arithmetic operations
            if vm.isnumber(a) and vm.isnumber(b) and c in arithmetic:
                # Although we can detect division by zero at compile time, we
                # don't report it here, because the surrounding system doesn't
                # handle that very well. So just leave it for now.  (NOTE: If
                # we had an "error" instruction, we could actually transform
                # the expression to an error, or exit instruction perhaps)
                if b==0 and c in divzero:
                    if ignore_errors:
                        continue
                    else:
                        raise CompileError(
                                ZeroDivisionError("Division by zero"))

                # Calculate result by running on a machine
                result = vm.Machine([a,b,c], optimize=False).run().top
                del code[i:i+3]
                code.insert(i, result)

                if not silent:
                    print("Optimizer: Constant-folded %d %d %s to %d" % (a,b,c,result))

                keep_running = True
                break

            # Translate <constant> dup to <constant> <constant>
            if vm.isconstant(a) and b == lookup(Instruction.dup):
                code[i+1] = a
                if not silent:
                    print("Optimizer: Translated %s %s to %s %s" % (a,b,a,a))
                keep_running = True
                break

            # Dead code removal: <constant> drop
            if vm.isconstant(a) and b == lookup(Instruction.drop):
                del code[i:i+2]
                if not silent:
                    print("Optimizer: Removed dead code %s %s" % (a,b))
                keep_running = True
                break

            # Dead code removal: <integer> cast_int
            if isinstance(a, int) and b == lookup(Instruction.cast_int):
                del code[i+1]
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a,b,a))
                keep_running = True
                break

            # Dead code removal: <string> cast_str
            if isinstance(a, str) and b == lookup(Instruction.cast_str):
                del code[i+1]
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a,b,a))
                keep_running = True
                break

            # Dead code removal: <boolean> cast_bool
            if isinstance(a, bool) and b == lookup(Instruction.cast_bool):
                del code[i+1]
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a,b,a))
                keep_running = True
                break

            # <c1> <c2> swap -> <c2> <c1>
            if vm.isconstant(a) and vm.isconstant(b) and c==lookup(Instruction.swap):
                del code[i:i+3]
                code = code[:i] + [b, a] + code[i:]
                if not silent:
                    print("Optimizer: Translated %s %s %s to %s %s" %
                            (a,b,c,b,a))
                keep_running = True
                break

            # a b over -> a b a
            if vm.isconstant(a) and vm.isconstant(b) and c==lookup(Instruction.over):
                code[i+2] = a
                if not silent:
                    print("Optimizer: Translated %s %s %s to %s %s %s" %
                            (a,b,c,a,b,a))
                keep_running = True
                break

            # "123" cast_int -> 123
            if vm.isstring(a) and b == lookup(Instruction.cast_int):
                try:
                    number = int(a[1:-1])
                    del code[i:i+2]
                    code.insert(i, number)
                    if not silent:
                        print("Optimizer: Translated %s %s to %s" % (a, b,
                            number))
                    keep_running = True
                    break
                except ValueError:
                    pass

            if vm.isconstant(a) and b == lookup(Instruction.cast_str):
                if vm.isstring(a):
                    asstring = a[1:-1]
                else:
                    asstring = str(a)
                asstring = '"%s"' % asstring
                del code[i:i+2]
                code.insert(i, asstring)
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a, b, asstring))
                keep_running = True
                break

            if vm.isconstant(a) and b == lookup(Instruction.cast_bool):
                v = a
                if vm.isstring(v):
                    v = v[1:-1]
                v = bool(v)
                del code[i:i+2]
                code.insert(i, v)
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a, b, v))
                keep_running = True
                break

    return code
