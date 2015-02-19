"""
A simple stack-based virtual machine that you can add your own instructions to.

Copyright (C) 2015 Christian Stigen Larsen
See the file LICENSE for the license text.
"""

import StringIO
import optparse
import string
import sys
import tokenize


__version__ = "0.2.0"


class MachineError(Exception):
    pass

class ParserError(Exception):
    pass

class CompilationError(Exception):
    pass


class Stack(object):
    def __init__(self):
        self._values = []

    def pop(self):
        if len(self._values) == 0:
            raise MachineError("Stack underflow")
        return self._values.pop()

    def push(self, value):
        self._values.append(value)

    @property
    def top(self):
        return None if len(self._values) == 0 else self._values[-1]

    def __str__(self):
        return str(self._values)

    def __repr__(self):
        return "<Stack: values=%s>" % self._values

    def __len__(self):
        return len(self._values)


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
        if vm.output is not None:
            vm.output.write(value)
            if flush:
                vm.output.flush()

    @staticmethod
    def at(vm):
        """Pushes previous position to return stack."""
        vm.return_stack.push(vm.instruction_pointer - 1)

    @staticmethod
    def dot(vm, flush=True):
        Instruction.write(vm, flush=False)
        if vm.output is not None:
            vm.output.write("\n")
            if flush:
                vm.output.flush()

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


class Machine(object):
    """A virtual machine engine."""

    def __init__(self, code, output=sys.stdout, optimize_code=True):
        self.reset()
        self._code = code if optimize_code == False else optimize(code)
        self.output = output
        self.instructions = Instruction.default_instructions

    def lookup(self, instruction):
        """Looks up name-to-function or function-to-name."""
        return Instruction.lookup(instruction, self.instructions)

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        self._code = optimize(value)

    @property
    def stack(self):
        """Returns the data (operand) stack values."""
        return self.data_stack._values

    def reset(self):
        self.data_stack = Stack()
        self.return_stack = Stack()
        self.instruction_pointer = 0
        return self

    def __repr__(self):
        return "<Machine: IP=%d |DS|=%d |RS|=%d>" % (self.instruction_pointer,
                len(self.data_stack), len(self.return_stack))

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
        return self.data_stack.pop()

    def push(self, value):
        self.data_stack.push(value)

    @property
    def top(self):
        return self.data_stack.top

    def step(self):
        """Executes one instruction and stops."""
        instruction = self.code[self.instruction_pointer]
        self.instruction_pointer += 1
        self.dispatch(instruction)

    def run(self, steps=None):
        """Run machine, dispatching instructions.

        If steps is specified, it will run that many instructions.
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


def parse(stream):
    """Parse a Forth-like language and return code."""
    code = []
    tokens = tokenize.generate_tokens(stream.readline)

    def strip_whitespace(s):
        r = ""
        for ch in s:
            if not ch in string.whitespace:
                r += ch
            else:
                r += "\\x%x" % ord(ch)
        return r

    while True:
        for token, value, _, _, _ in tokens:
            if token == tokenize.NUMBER:
                try:
                    code.append(int(value))
                except ValueError, e:
                    raise ParserError(e)
            elif token in [tokenize.OP, tokenize.STRING, tokenize.NAME]:
                code.append(value)
#            elif token == tokenize.ERRORTOKEN:
#                if value == '!':
#                    code.append(lookup(Instruction.binary_not))
            elif token in [tokenize.NEWLINE, tokenize.NL]:
                break
            elif token in [tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT]:
                pass
            elif token == tokenize.ENDMARKER:
                return code
            else:
                raise ParserError("Unknown token %s: '%s'" %
                        (tokenize.tok_name[token], strip_whitespace(value)))
    return code

def lookup(instruction):
    return Instruction.lookup(instruction)

def check(code):
    """Checks code for obvious errors."""
    def safe_lookup(op):
        try:
            return lookup(op)
        except Exception:
            return op

    for i, a in enumerate(code):
        b = code[i+1] if i+1 < len(code) else None
        c = code[i+2] if i+2 < len(code) else None

        # Does instruction exist?
        if not isconstant(a):
            try:
                lookup(a)
            except Exception, e:
                raise CompilationError(e)

        # Invalid: <str> int
        if isstring(a) and safe_lookup(b) == Instruction.cast_int:
            raise CompilationError(
                "Cannot convert string to integer (index %d): %s %s" % (i, a,
                    b))

        # Invalid: <int> <binary op>
        binary_ops = [Instruction.binary_not,
                      Instruction.binary_or,
                      Instruction.binary_and]
        if not isbool(a) and safe_lookup(b) in binary_ops:
            raise CompilationError(
                "Can only use binary operators on booleans (index %d): %s %s" %
                    (i, a, b))

    return code

def compile(code, silent=True, ignore_errors=False, optimize_code=True):
    """Compiles subroutine-forms into a complete working code.

    A program such as:

        :sub1 <sub1 code ...> ;
        :sub2 <sub2 code ...> ;
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

        optimize_code: Flag to control whether to optimize code.

    Raises:
        CompilationError - Raised if invalid code is detected.

    Returns:
        An array of code that can be run by a Machine. Typically, you want to
        pass this to a Machine without doing optimizations.

    Usage:
        source = parse(StringIO.StringIO("<source code>"))
        code = compile(source)
        machine = Machine(code, optimize_code=False)
        machine.run()
    """

    output = []
    subroutine = {}
    builtins = Machine([]).instructions

    try:
        it = code.__iter__()
        while True:
            word = it.next()
            if word == ":":
                name = it.next()
                if name in builtins:
                    raise CompilationError("Cannot shadow internal word definition '%s'." % name)
                if name in [":", ";"]:
                    raise CompilationError("Invalid word name '%s'." % name)
                subroutine[name] = []
                while True:
                    op = it.next()
                    if op == ";":
                        subroutine[name].append(lookup(Instruction.return_))
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
                xcode.append(lookup(Instruction.call))
        subroutine[name] = xcode

    # Compile main code (code outside of subroutines)
    xcode = []
    for op in output:
        xcode.append(op)
        if op in subroutine:
            xcode.append(lookup(Instruction.call))

    # Because main code comes before subroutines, we need to explicitly add an
    # exit instruction
    output = xcode
    if len(subroutine) > 0:
        output += [lookup(Instruction.exit)]

    # Optimize main code
    if optimize_code:
        output = optimize(output, silent=silent, ignore_errors=False)

    # Add subroutines to output, track their locations
    location = {}
    for name, code in subroutine.items():
        location[name] = len(output)
        if optimize_code:
            output += optimize(code, silent=silent, ignore_errors=False)
        else:
            output += code

    # Resolve all subroutine references
    for i, op in enumerate(output):
        if op in location:
            output[i] = location[op]

    return check(output)

def optimize(code, silent=True, ignore_errors=True):
    """Performs optimizations on already parsed code."""
    return constant_fold(code, silent=silent, ignore_errors=ignore_errors)

def isstring(c):
    return isinstance(c, str) and c[0]==c[-1]=='"'

def isnumber(c):
    return isinstance(c, int) or isinstance(c, long) or isinstance(c,
            float)

def isbool(c):
    return isinstance(c, bool) or c in [lookup(Instruction.true_),
            lookup(Instruction.false_)]

def isbinary(c):
    """True if c can be part of binary/bitwise operations."""
    return isnumber(c) or isbool(c)

def isconstant(c):
    return isbool(c) or isnumber(c) or isstring(c)


def constant_fold(code, silent=True, ignore_errors=True):
    """Constant-folds simple expressions like 2 3 + to 5."""

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
                        raise CompilationError(
                                ZeroDivisionError("Division by zero"))

                # Calculate result by running on a machine
                result = Machine([a,b,c], optimize_code=False).run().top
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


def repl(optimize_code=True, persist=True):
    """Starts a simple REPL for this machine."""

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

            code = compile(parse(StringIO.StringIO(source)), silent=False,
                    optimize_code=optimize_code)

            if not persist:
                machine.reset()

            machine.code += code
            machine.run()
        except EOFError:
            return
        except KeyboardInterrupt:
            return
        except ParserError, e:
            print("Parser error: %s" % e)
        except MachineError, e:
            print("Machine error: %s" % e)
        except Exception, e:
            print("Error: %s" % e)


if __name__ == "__main__":
    try:
        opt = optparse.OptionParser("Usage: %prog [option(s)] [file(s])",
                version="%prog " + __version__)

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
                            ignore_errors=False, optimize_code=opts.optimize)
                    machine = Machine(code, optimize_code=False)
                    if not opts.dump:
                        machine.run()
                    else:
                        print(machine.code_string)
                except MachineError, e:
                    print("Runtime error: %s" % e)
                    sys.exit(1)
                except CompilationError, e:
                    print("Compile error: %s" % e)
                    sys.exit(1)
                except ParserError, e:
                    print("Parser error: %s" % e)
                    sys.exit(1)
    except KeyboardInterrupt:
        pass
