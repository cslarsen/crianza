"""
A simple stack-based virtual machine that you can add your own instructions to.

Copyright (C) 2015 Christian Stigen Larsen
See the file LICENSE for the license text.
"""

import optparse
import sys

from errors import (CompileError, MachineError, ParseError)
from instructions import (Instruction, lookup)
from parser import parse
from stack import Stack
import crianza


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
        self._code = code if optimize == False else optimized(code)
        self._optimize = optimize
        self.output = output
        self.instructions = Instruction.default_instructions

    def lookup(self, instruction):
        """Looks up name-to-function or function-to-name."""
        return Instruction.lookup(instruction, self.instructions)

    @property
    def code(self):
        """The machine's code."""
        return self._code

    @code.setter
    def code(self, value):
        self._code = value if not self._optimize else optimized(value)

    @property
    def stack(self):
        """Returns the data (operand) stack values."""
        return self.data_stack._values

    def reset(self):
        """Reset stacks and instruction pointer."""
        self.data_stack = Stack()
        self.return_stack = Stack()
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


def optimized(code, silent=True, ignore_errors=True):
    """Performs optimizations on already parsed code."""
    return constant_fold(code, silent=silent, ignore_errors=ignore_errors)

def isstring(c):
    """Checks if value is a quoted string."""
    return isinstance(c, str) and c[0]==c[-1]=='"'

def isnumber(c):
    """Checks if value is an integer, long integer or float."""
    return isinstance(c, int) or isinstance(c, long) or isinstance(c,
            float)

def isbool(c):
    """Checks if value is boolean."""
    return isinstance(c, bool) or c in [lookup(Instruction.true_),
            lookup(Instruction.false_)]

def isbinary(c):
    """Checks if value can be part of binary/bitwise operations."""
    return isnumber(c) or isbool(c)

def isconstant(c):
    """Checks if value is a boolean, number or string."""
    return isbool(c) or isnumber(c) or isstring(c)


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
            if isnumber(a) and isnumber(b) and c in arithmetic:
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
                result = Machine([a,b,c], optimize=False).run().top
                del code[i:i+3]
                code.insert(i, result)

                if not silent:
                    print("Optimizer: Constant-folded %d %d %s to %d" % (a,b,c,result))

                keep_running = True
                break

            # Translate <constant> dup to <constant> <constant>
            if isconstant(a) and b == lookup(Instruction.dup):
                code[i+1] = a
                if not silent:
                    print("Optimizer: Translated %s %s to %s %s" % (a,b,a,a))
                keep_running = True
                break

            # Dead code removal: <constant> drop
            if isconstant(a) and b == lookup(Instruction.drop):
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
            if isconstant(a) and isconstant(b) and c==lookup(Instruction.swap):
                del code[i:i+3]
                code = code[:i] + [b, a] + code[i:]
                if not silent:
                    print("Optimizer: Translated %s %s %s to %s %s" %
                            (a,b,c,b,a))
                keep_running = True
                break

            # a b over -> a b a
            if isconstant(a) and isconstant(b) and c==lookup(Instruction.over):
                code[i+2] = a
                if not silent:
                    print("Optimizer: Translated %s %s %s to %s %s %s" %
                            (a,b,c,a,b,a))
                keep_running = True
                break

            # "123" cast_int -> 123
            if isstring(a) and b == lookup(Instruction.cast_int):
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

            if isconstant(a) and b == lookup(Instruction.cast_str):
                if isstring(a):
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

            if isconstant(a) and b == lookup(Instruction.cast_bool):
                v = a
                if isstring(v):
                    v = v[1:-1]
                v = bool(v)
                del code[i:i+2]
                code.insert(i, v)
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a, b, v))
                keep_running = True
                break

    return code

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

def repl(optimize=True, persist=True):
    """Starts a simple REPL for this machine.

    Args:
        optimize: Controls whether to run inputted code through the
        optimizer.

        persist: If True, the machine is not deleted after each line.
    """

    def print_code(vm, ops_per_line=8):
        """Prints code and state for VM."""
        print("IP: %d" % vm.instruction_pointer)
        print("DS: %s" % str(vm.stack))
        print("RS: %s" % str(vm.return_stack))

        for addr, op in enumerate(vm.code):
            if (addr % ops_per_line) == 0 and (addr+1) < len(vm.code):
                if addr > 0:
                    sys.stdout.write("\n")
                sys.stdout.write("%0*d  " % (max(4, len(str(len(vm.code)))), addr))
            value = str(op)
            if isstring(op):
                value = repr(op)[1:-1]
            sys.stdout.write("%s " % value)
        sys.stdout.write("\n")

    print("Extra commands for the REPL:")
    print(".code    - print code")
    print(".quit    - exit immediately")
    print(".reset   - reset machine (IP and stacks)")
    print(".restart - create a clean, new machine")
    print("")

    machine = Machine([])

    while True:
        try:
            source = raw_input("> ").strip()

            if source == ".quit":
                return
            elif source == ".code":
                print_code(machine)
                continue
            elif source == ".reset":
                machine.reset()
                continue
            elif source == ".restart":
                machine = Machine([])
                continue

            code = compile(parse(source), silent=False, optimize=optimize)

            if not persist:
                machine.reset()

            machine.code += code
            machine.run()
        except EOFError:
            return
        except KeyboardInterrupt:
            return
        except ParseError, e:
            print("Parser error: %s" % e)
        except MachineError, e:
            print("Machine error: %s" % e)
        except Exception, e:
            print("Error: %s" % e)


if __name__ == "__main__":
    try:
        opt = optparse.OptionParser("Usage: %prog [option(s)] [file(s])",
                version="%prog " + crianza.__version__)

        opt.add_option("-d", "--dump", dest="dump",
            help="Dump machine code and exit.",
            action="store_true", default=False)

        opt.add_option("-v", "--verbose", dest="verbose",
            help="Enable verbose output.",
            action="store_true", default=False)

        opt.add_option("-x", dest="optimize",
            help="Do not optimize program.",
            action="store_false", default=True)

        opt.add_option("-r", "--repl", dest="repl",
            help="Enter REPL.",
            action="store_true", default=False)

        opt.disable_interspersed_args()
        (opts, args) = opt.parse_args()

        if opts.repl:
            repl()
            sys.exit(0)

        if len(args) == 0:
            opt.print_help()
            sys.exit(1)

        for name in args:
            with open(name, "rt") as file:
                try:
                    code = parse(file)
                    code = compile(code, silent=not opts.verbose,
                            ignore_errors=False, optimize=opts.optimize)
                    machine = Machine(code, optimize=False)
                    if not opts.dump:
                        machine.run()
                    else:
                        print(machine.code_string)
                except MachineError, e:
                    print("Runtime error: %s" % e)
                    sys.exit(1)
                except CompileError, e:
                    print("Compile error: %s" % e)
                    sys.exit(1)
                except ParseError, e:
                    print("Parser error: %s" % e)
                    sys.exit(1)
    except KeyboardInterrupt:
        pass
