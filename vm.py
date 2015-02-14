"""
A simple stack-based virtual machine that you can add your own instructions to.
"""

from StringIO import StringIO
from tokenize import *
import string
import sys


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
        return self._values[-1]

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
            if not (isinstance(arg, int) or isinstance(arg, long)):
                raise MachineError("Not an integer: %s" % str(arg))

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
    def exit(vm):
        raise StopIteration

    @staticmethod
    def dup(vm):
        a = vm.pop()
        vm.push(a)
        vm.push(a)

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
        vm.push(int(vm.pop()))

    @staticmethod
    def cast_str(vm):
        vm.push(str(vm.pop()))

    @staticmethod
    def eq(vm):
        vm.push(vm.pop() == vm.pop())

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
        if isinstance(test, bool) and test == False:
            result = False
        elif isinstance(test, str) and len(test) == 0:
            result = False
        elif isinstance(test, int) and test == 0:
            result = False
        else:
            result = True

        if result == True:
            vm.push(true_clause)
        else:
            vm.push(false_clause)

    @staticmethod
    def jmp(vm):
        address = vm.pop()
        if isinstance(address, int) and (0 <= address < len(vm.code)):
            vm.instruction_pointer = address
        else:
            raise MachineError("Jump addressess must be a valid integer: %s" %
                    str(address))

    @staticmethod
    def dump_stack(vm):
        vm.output.write("Data stack:\n")
        for v in reversed(vm.data_stack._values):
            vm.output.write(" - type %s, value '%s'\n" % (type(v), v))

        vm.output.write("Return stack:\n")
        for v in reversed(vm.return_stack._values):
            vm.output.write(" - address %s\n" % str(v))

        vm.output.flush()


class Machine(object):
    """A virtual machine engine."""
    def __init__(self, code, output=sys.stdout, optimize_code=True):
        self.reset()
        self._code = code if optimize_code == False else optimize(code)
        self.output = output

        self.instructions = {
            "%":        Instruction.mod,
            "*":        Instruction.mul,
            "+":        Instruction.add,
            "-":        Instruction.sub,
            ".":        Instruction.dot,
            "/":        Instruction.div,
            "<":        Instruction.less,
            "==":       Instruction.eq,
            ">":        Instruction.greater,
            "@":        Instruction.at,
            "add":      Instruction.add,
            "call":     Instruction.call,
            "cast_int": Instruction.cast_int,
            "cast_str": Instruction.cast_str,
            "div":      Instruction.div,
            "drop":     Instruction.drop,
            "dup":      Instruction.dup,
            "exit":     Instruction.exit,
            "false":    Instruction.false_,
            "if":       Instruction.if_stmt,
            "jmp":      Instruction.jmp,
            "mod":      Instruction.mod,
            "mul":      Instruction.mul,
            "over":     Instruction.over,
            "read":     Instruction.read,
            "return":   Instruction.return_,
            "stack":    Instruction.dump_stack,
            "sub":      Instruction.sub,
            "swap":     Instruction.swap,
            "true":     Instruction.true_,
            "write":    Instruction.write,
        }

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
        return "<Machine: IP=%d |DS|=%d |RS|=%d |code|=%d>" % (
            self.instruction_pointer, len(self.data_stack),
            len(self.return_stack), len(self.code))

    def __str__(self):
        return self.__repr__()

    @property
    def code_string(self):
        """Returns code as a parseable string."""
        s = []
        for op in self.code:
            if isinstance(op, str) and op[0]==op[-1]=='"':
                s.append(repr(op))
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

    def run(self):
        try:
            while self.instruction_pointer < len(self.code):
                self.step()
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
        elif isinstance(op, int):
            # Push numbers on data stack
            self.push(op)
        elif isinstance(op, str) and op[0]==op[-1]=='"':
            # Push quoted string on data stack
            self.push(op[1:-1])
        else:
            raise MachineError("Unknown instruction '%s' at index %d" %
                    (op, self.instruction_pointer))


def parse(stream):
    """Parse a Forth-like language and return code."""
    code = []
    tokens = generate_tokens(stream.readline)

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
            if token == NUMBER:
                try:
                    code.append(int(value))
                except ValueError, e:
                    raise ParserError(e)
            elif token in [OP, STRING, NAME]:
                code.append(value)
            elif token in [NEWLINE, NL]:
                break
            elif token in [COMMENT, INDENT, DEDENT]:
                pass
            elif token == ENDMARKER:
                return code
            else:
                raise ParserError("Unknown token %s: '%s'" %
                        (tok_name[token], strip_whitespace(value)))
    return code

def compile(code, silent=True, ignore_errors=False, optimize_code=True):
    """Translates subroutine-forms into a complete working code."""

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
                    raise CopmilationError("Invalid word name '%s'." % name)
                subroutine[name] = []
                while True:
                    op = it.next()
                    if op == ";":
                        subroutine[name].append("return")
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
                xcode.append("call")
        subroutine[name] = xcode

    # Add main code (code outside of subroutines)
    xcode = []
    for op in output:
        xcode.append(op)
        if op in subroutine:
            xcode.append("call")

    # Because main code comes before subroutines, we need to explicitly add an
    # exit instruction
    output = xcode
    if len(subroutine) > 0:
        output += ["exit"]

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

    return output

def optimize(code, silent=True, ignore_errors=True):
    """Performs optimizations on already parsed code."""
    return constant_fold(code, silent=silent, ignore_errors=ignore_errors)

def constant_fold(code, silent=True, ignore_errors=True):
    """Constant-folds simple expressions like 2 3 + to 5."""

    # Loop until we haven't done any optimizations.  E.g., "2 3 + 5 *" will be
    # optimized to "5 5 *" and in the next iteration to 25.

    arithmetic = ["+", "-", "*", "/", "%", "add", "sub", "mul", "div", "mod",
                  ">", "==", "<"]

    def isstring(c):
        return isinstance(c, str) and c[0]==c[-1]=='"'

    def isnumber(c):
        return isinstance(c, int) or isinstance(c, long) or isinstance(c,
                float)

    def isbool(c):
        return isinstance(c, bool)

    def isconstant(c):
        return isbool(c) or isnumber(c) or isstring(c)

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
                if b==0 and c in ["%", "mod", "div", "/"]:
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
            if isconstant(a) and b == "dup":
                code[i+1] = a
                if not silent:
                    print("Optimizer: Translated %s %s to %s %s" % (a,b,a,a))
                keep_running = True
                break

            # Remove dead code such as <constant> drop
            if isconstant(a) and b == "drop":
                del code[i:i+2]
                if not silent:
                    print("Optimizer: Removed dead code %s %s" % (a,b))
                keep_running = True
                break

            # <c1> <c2> swap -> <c2> <c1>
            if isconstant(a) and isconstant(b) and c == "swap":
                del code[i:i+3]
                code = code[:i] + [b, a] + code[i:]
                if not silent:
                    print("Optimizer: Translated %s %s %s to %s %s" %
                            (a,b,c,b,a))
                keep_running = True
                break

            # "123" cast_int -> 123
            if isstring(a) and b == "cast_int":
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

            if isnumber(a) and b == "cast_str":
                string = '"%s"' % str(a)
                del code[i:i+2]
                code.insert(i, string)
                if not silent:
                    print("Optimizer: Translated %s %s to %s" % (a, b, string))
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
        sys.stdout.write("%s " % str(op))
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

            code = compile(parse(StringIO(source)), silent=False,
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
        if len(sys.argv) == 1:
            repl()
            sys.exit(0)

        for name in sys.argv[1:]:
            with open(name, "rt") as file:
                code = parse(file)
                code = compile(code, silent=True, ignore_errors=False)
                Machine(code, optimize_code=False).run()

    except KeyboardInterrupt:
        pass
