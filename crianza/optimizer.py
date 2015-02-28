import errors
import instructions
import interpreter


def optimized(code, silent=True, ignore_errors=True):
    """Performs optimizations on already parsed code."""
    return constant_fold(code, silent=silent, ignore_errors=ignore_errors)

def constant_fold(code, silent=True, ignore_errors=True):
    """Constant-folds simple expressions like 2 3 + to 5.

    Args:
        code: Code in non-native types.
        silent: Flag that controls whether to print optimizations made.
        ignore_errors: Whether to raise exceptions on found errors.
    """
    # Loop until we haven't done any optimizations.  E.g., "2 3 + 5 *" will be
    # optimized to "5 5 *" and in the next iteration to 25.  Yes, this is
    # extremely slow, big-O wise. We'll fix that some other time. (TODO)

    arithmetic = map(instructions.lookup, [
        instructions.add,
        instructions.bitwise_and,
        instructions.bitwise_or,
        instructions.bitwise_xor,
        instructions.div,
        instructions.equal,
        instructions.greater,
        instructions.less,
        instructions.mod,
        instructions.mul,
        instructions.sub,
    ])

    divzero = map(instructions.lookup, [
        instructions.div,
        instructions.mod,
    ])

    lookup = instructions.lookup

    def isfunction(op):
        try:
            instructions.lookup(op)
            return True
        except KeyError:
            return False

    def isconstant(op):
        return op is None or interpreter.isconstant(op, quoted=True) or not isfunction(op)

    keep_running = True
    while keep_running:
        keep_running = False
        # Find two consecutive numbes and an arithmetic operator
        for i, a in enumerate(code):
            b = code[i+1] if i+1 < len(code) else None
            c = code[i+2] if i+2 < len(code) else None

            #print("-- a=%s b=%s c=%s lookup=%s" % (a,b,c,lookup(c)))

            # Constant fold arithmetic operations (TODO: Move to check-func)
            if interpreter.isnumber(a, b) and c in arithmetic:
                # Although we can detect division by zero at compile time, we
                # don't report it here, because the surrounding system doesn't
                # handle that very well. So just leave it for now.  (NOTE: If
                # we had an "error" instruction, we could actually transform
                # the expression to an error, or exit instruction perhaps)
                if b==0 and c in divzero:
                    if ignore_errors:
                        continue
                    else:
                        raise errors.CompileError(ZeroDivisionError(
                            "Division by zero"))

                # Calculate result by running on a machine (lambda vm: ... is
                # embedded pushes, see compiler)
                result = interpreter.Machine([lambda vm: vm.push(a), lambda vm:
                    vm.push(b), instructions.lookup(c)]).run().top
                del code[i:i+3]
                code.insert(i, result)

                if not silent:
                    print("Optimizer: Constant-folded %d %d %s to %d" % (a,b,c,result))

                keep_running = True
                break

            # Translate <constant> dup to <constant> <constant>
            if isconstant(a) and b == lookup(instructions.dup):
                code[i+1] = a
                if not silent:
                    print("Optimizer: Translated %s %s to %s %s" % (a,b,a,a))
                keep_running = True
                break

            # Dead code removal: <constant> drop
            if isconstant(a) and b == lookup(instructions.drop):
                del code[i:i+2]
                if not silent:
                    print("Optimizer: Removed dead code %s %s" % (a,b))
                keep_running = True
                break

            if a == lookup(instructions.nop):
                del code[i]
                if not silent:
                    print("Optimizer: Removed dead code %s" % a)
                keep_running = True
                break

            # Dead code removal: <integer> cast_int
            if isinstance(a, int) and b == lookup(instructions.cast_int):
                del code[i+1]
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a,b,a))
                keep_running = True
                break

            # Dead code removal: <string> cast_str
            if isinstance(a, str) and b == lookup(instructions.cast_str):
                del code[i+1]
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a,b,a))
                keep_running = True
                break

            # Dead code removal: <boolean> cast_bool
            if isinstance(a, bool) and b == lookup(instructions.cast_bool):
                del code[i+1]
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a,b,a))
                keep_running = True
                break

            # <c1> <c2> swap -> <c2> <c1>
            if isconstant(a) and isconstant(b) and c == lookup(instructions.swap):
                del code[i:i+3]
                code = code[:i] + [b, a] + code[i:]
                if not silent:
                    print("Optimizer: Translated %s %s %s to %s %s" %
                            (a,b,c,b,a))
                keep_running = True
                break

            # a b over -> a b a
            if isconstant(a) and isconstant(b) and c == lookup(instructions.over):
                code[i+2] = a
                if not silent:
                    print("Optimizer: Translated %s %s %s to %s %s %s" %
                            (a,b,c,a,b,a))
                keep_running = True
                break

            # "123" cast_int -> 123
            if interpreter.isstring(a) and b == lookup(instructions.cast_int):
                try:
                    number = int(a)
                    del code[i:i+2]
                    code.insert(i, number)
                    if not silent:
                        print("Optimizer: Translated %s %s to %s" % (a, b,
                            number))
                    keep_running = True
                    break
                except ValueError:
                    pass

            if isconstant(a) and b == lookup(instructions.cast_str):
                del code[i:i+2]
                code.insert(i, str(a))
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a, b, str(a)))
                keep_running = True
                break

            if isconstant(a) and b == lookup(instructions.cast_bool):
                del code[i:i+2]
                code.insert(i, bool(a))
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a, b, bool(a)))
                keep_running = True
                break
    return code
