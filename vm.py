#!/usr/bin/env python

from StringIO import StringIO
from tokenize import *
import string
import sys

class MachineError(Exception):
    pass


class ParserError(Exception):
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

    def __len__(self):
        return len(self._values)


class Machine(object):
    def __init__(self, code, stdout=sys.stdout, optimize=True):
        self.reset()
        self._code = code if optimize == False else constant_fold(code)
        self.stdout = stdout

        self.dispatch_map = {
            "%":        self.mod,
            "*":        self.mul,
            "+":        self.add,
            "-":        self.sub,
            ".":        self.dot,
            "/":        self.div,
            "<":        self.less,
            "==":       self.eq,
            ">":        self.greater,
            "@":        self.at,
            "add":      self.add,
            "call":     self.call,
            "cast_int": self.cast_int,
            "cast_str": self.cast_str,
            "div":      self.div,
            "drop":     self.drop,
            "dup":      self.dup,
            "exit":     self.exit,
            "false":    self.false_,
            "if":       self.if_stmt,
            "jmp":      self.jmp,
            "mod":      self.mod,
            "mul":      self.mul,
            "over":     self.over,
            "read":     self.read,
            "return":   self.return_,
            "stack":    self.dump_stack,
            "sub":      self.sub,
            "swap":     self.swap,
            "true":     self.true_,
            "write":    self.write,
        }

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value):
        self._code = constant_fold(value)

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
        if op in self.dispatch_map:
            self.dispatch_map[op]()
        elif isinstance(op, int):
            # Push numbers on data stack
            self.push(op)
        elif isinstance(op, str) and op[0]==op[-1]=='"':
            # Push quoted string on data stack
            self.push(op[1:-1])
        else:
            raise MachineError("Unknown instruction '%s' at index %d" %
                    (op, self.instruction_pointer))

    def _assert_int(self, *args):
        for arg in args:
            if not (isinstance(arg, int) or isinstance(arg, long)):
                raise MachineError("Not an integer: %s" % str(arg))

    def add(self):
        a = self.pop()
        b = self.pop()
        self._assert_int(a, b)
        self.push(a + b)

    def sub(self):
        a = self.pop()
        b = self.pop()
        self._assert_int(a, b)
        self.push(b - a)

    def call(self):
        self.return_stack.push(self.instruction_pointer)
        self.jmp()

    def return_(self):
        self.instruction_pointer = self.return_stack.pop()

    def mul(self, modulus=None):
        a = self.pop()
        b = self.pop()
        self._assert_int(a, b)

        if modulus is None:
            self.push(a * b)
        else:
            self.push((a * b) % modulus)

    def div(self):
        divisor = self.pop()
        dividend = self.pop()
        self._assert_int(dividend, divisor)
        if divisor == 0:
            raise MachineError("Divide by zero")
        self.push(dividend / divisor)

    def mod(self):
        a = self.pop()
        b = self.pop()
        self._assert_int(a, b)
        self.push(b % a)

    def exit(self):
        raise StopIteration

    def dup(self):
        a = self.pop()
        self.push(a)
        self.push(a)

    def over(self):
        b = self.pop()
        a = self.pop()
        self.push(a)
        self.push(b)
        self.push(a)

    def drop(self):
        self.pop()

    def swap(self):
        b = self.pop()
        a = self.pop()
        self.push(b)
        self.push(a)

    def write(self):
        self.stdout.write(str(self.pop()))
        self.stdout.flush()

    def at(self):
        self.return_stack.push(self.instruction_pointer - 1)

    def dot(self, flush=True):
        self.write()
        self.stdout.write("\n")
        if flush:
            self.stdout.flush()

    def read(self):
        self.push(raw_input())

    def cast_int(self):
        self.push(int(self.pop()))

    def cast_str(self):
        self.push(str(self.pop()))

    def eq(self):
        self.push(self.pop() == self.pop())

    def less(self):
        a = self.pop()
        self.push(a < self.pop())

    def greater(self):
        a = self.pop()
        self.push(a > self.pop())

    def true_(self):
        self.push(True)

    def false_(self):
        self.push(False)

    def if_stmt(self):
        false_clause = self.pop()
        true_clause = self.pop()
        test = self.pop()

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
            self.push(true_clause)
        else:
            self.push(false_clause)

    def jmp(self):
        addr = self.pop()
        if isinstance(addr, int) and addr >= 0 and addr < len(self.code):
            self.instruction_pointer = addr
        else:
            raise MachineError("Jump address must be a valid integer.")

    def dump_stack(self):
        self.stdout.write("Data stack:\n")
        for v in reversed(self.data_stack._values):
            self.stdout.write(" - type %s, value '%s'\n" % (type(v), v))

        self.stdout.write("Return stack:\n")
        for v in reversed(self.return_stack._values):
            self.stdout.write(" - address %s\n" % str(v))

        self.stdout.flush()


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

def translate(code, dump_source=False):
    """Translates stuff such as subroutines etc into a complete working
    code."""

    output = []
    subroutine = {}
    builtins = Machine([]).dispatch_map

    try:
        it = code.__iter__()
        while True:
            word = it.next()
            if word == ":":
                name = it.next()
                if name in builtins:
                    raise ParserError("Cannot shadow internal word definition '%s'." % name)
                if name in [":", ";"]:
                    raise ParserError("Invalid word name '%s'." % name)
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

    xcode = []
    for op in output:
        xcode.append(op)
        if op in subroutine:
            xcode.append("call")

    output = xcode
    if len(subroutine) > 0:
        output += ["exit"]

    # Add subroutines to output, track their locations
    location = {}
    for name, code in subroutine.items():
        location[name] = len(output)
        output += code

    # Resolve all subroutine references
    for i, op in enumerate(output):
        if op in location:
            output[i] = location[op]

    if dump_source:
        revloc = dict(((b,a) for a,b in location.items()))
        prev = None
        width = len(str(len(output)))
        for i, op in enumerate(output):
            if i in revloc:
                name = revloc[i]
                print("\n%s:" % name)
            if op == "call":
                print("  %.*d %s (%s)" % (width, i, op, revloc[prev]))
            else:
                print("  %.*d %s" % (width, i, op))
            prev = op

    return output

def constant_fold(code, silent=True):
    """Constant-folds simple expressions like 2 3 + to 5."""

    # Loop until we haven't done any optimizations.  E.g., "2 3 + 5 *" will be
    # optimized to "5 5 *" and in the next iteration to 25.

    arithmetic = ["+", "-", "*", "/", "%", "add", "sub", "mul", "div", "mod"]

    isconstant = lambda c: isinstance(c, int) or isinstance(c, str) or isinstance(c, bool)

    keep_running = True
    while keep_running:
        keep_running = False
        # Find two consecutive numbes and an arithmetic operator
        for i, a in enumerate(code):
            b = code[i+1] if i+1 < len(code) else None
            c = code[i+2] if i+2 < len(code) else None

            # Constant fold arithmetic operations
            if isinstance(a, int) and isinstance(b, int) and c in arithmetic:
                result = Machine([a,b,c], optimize=False).run().top
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


def repl(optimize=True, persist=True):
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

            code = translate(parse(StringIO(source)))

            if optimize:
                code = constant_fold(code, silent=False)

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

        dump_source = False

        for name in sys.argv[1:]:
            with open(name, "rt") as file:
                Machine(translate(parse(file), dump_source)).run()

    except KeyboardInterrupt:
        pass
