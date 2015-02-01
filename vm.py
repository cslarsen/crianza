#!/usr/bin/env python

from StringIO import StringIO
import sys
import tokenize

class Stack:
    def __init__(self):
        self._values = []

    def pop(self):
        if len(self._values) == 0:
            raise RuntimeError("Stack underflow")
        return self._values.pop()

    def push(self, value):
        self._values.append(value)

    def top(self):
        return self._values[-1]


class Machine:
    def __init__(self, code):
        self.data_stack = Stack()
        self.return_stack = Stack()
        self.instruction_pointer = 0
        self.code = code

    def pop(self):
        return self.data_stack.pop()

    def push(self, value):
        self.data_stack.push(value)

    def top(self):
        return self.data_stack.top()

    def run(self):
        while self.instruction_pointer < len(self.code):
            opcode = self.code[self.instruction_pointer]
            self.instruction_pointer += 1
            self.dispatch(opcode)

    def dispatch(self, op):
        dispatch_map = {
            "%":        self.mod,
            "*":        self.mul,
            "+":        self.plus,
            "-":        self.minus,
            "/":        self.div,
            "==":       self.eq,
            "cast_int": self.cast_int,
            "cast_str": self.cast_str,
            "drop":     self.drop,
            "dup":      self.dup,
            "if":       self.if_stmt,
            "jmp":      self.jmp,
            "over":     self.over,
            "print":    self.print_,
            "println":  self.println,
            "read":     self.read,
            "stack":    self.dump_stack,
            "swap":     self.swap,
        }

        if op in dispatch_map:
            dispatch_map[op]()
        else:
            if isinstance(op, int):
                self.push(op) # push numbers on stack
            elif isinstance(op, str) and op[0]==op[-1]=='"':
                self.push(op[1:-1]) # push quoted strings on stack
            else:
                raise RuntimeError("Unknown opcode: '%s'" % op)

    # OPERATIONS FOLLOW:

    def plus(self):
        self.push(self.pop() + self.pop())

    def minus(self):
        last = self.pop()
        self.push(self.pop() - last)

    def mul(self):
        self.push(self.pop() * self.pop())

    def div(self):
        last = self.pop()
        self.push(self.pop() / last)

    def mod(self):
        last = self.pop()
        self.push(self.pop() % last)

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

    def print_(self):
        sys.stdout.write(str(self.pop()))
        sys.stdout.flush()

    def println(self):
        self.print_()
        sys.stdout.write("\n")
        sys.stdout.flush()

    def read(self):
        self.push(raw_input())

    def cast_int(self):
        self.push(int(self.pop()))

    def cast_str(self):
        self.push(str(self.pop()))

    def eq(self):
        self.push(self.pop() == self.pop())

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
            raise RuntimError("JMP address must be a valid integer.")

    def dump_stack(self):
        print("Data stack (top first):")

        for v in reversed(self.data_stack._values):
            print(" - type %s, value '%s'" % (type(v), v))


def examples():
    print("** Program 1: Runs the code for `print((2+3)*4)`")
    Machine([2, 3, "+", 4, "*", "println"]).run()

    print("\n** Program 2: Ask for numbers, computes sum and product.")
    Machine([
        '"Enter a number: "', "print", "read", "cast_int",
        '"Enter another number: "', "print", "read", "cast_int",
        "over", "over",
        '"Their sum is: "', "print", "+", "println",
        '"Their product is: "', "print", "*", "println"
    ]).run()

    print("\n** Program 3: Shows branching and looping (use CTRL+D to exit).")
    Machine([
        '"Enter a number: "', "print", "read", "cast_int",
        '"The number "', "print", "dup", "print", '" is "', "print",
        2, "%", 0, "==", '"even."', '"odd."', "if", "println",
        0, "jmp" # loop forever!
    ]).run()

def parse(text):
    code = []
    tokens = tokenize.generate_tokens(StringIO(text).readline)
    for toknum, tokval, _, _, _ in tokens:
        if toknum == tokenize.NUMBER:
            code.append(int(tokval))
        elif toknum in [tokenize.OP, tokenize.STRING, tokenize.NAME]:
            code.append(tokval)
        elif toknum == tokenize.ENDMARKER:
            break
        else:
            raise RuntimeError("Unknown token %s: '%s'" %
                    (tokenize.tok_name[toknum], tokval))
    return code

def constant_fold(code):
    """Constant-folds simple expressions like 2 3 + to 5."""

    # Loop until we haven't done any optimizations.  E.g., "2 3 + 5 *" will be
    # optimized to "5 5 *" and in the next iteration to 25.

    keep_running = True
    while keep_running:
        keep_running = False
        # Find two consecutive numbes and an arithmetic operator
        for i, ops in enumerate(zip(code, code[1:], code[2:])):
            a, b, op = ops
            if type(a)==type(b)==int and op in ["+", "-", "*", "/"]:
                m = Machine(ops)
                m.run()
                result = m.top()
                del code[i:i+3]
                code.insert(i, result)
                keep_running = True
                print("Optimizer: Constant-folded %d%s%d to %d" % (a,op,b,result))
                break
    return code

def repl():
    while True:
        source = raw_input("> ")
        code = parse(source)
        code = constant_fold(code)
        Machine(code).run()

def test_optimizer(code = [2, 3, "+", 5, "*", "println"]):
    print("Code before optimization: %s" % str(code))
    optimized = constant_fold(code)
    print("Code after optimization: %s" % str(optimized))

    print("Stack after running original program:")
    a = Machine(code)
    a.run()
    a.dump_stack()

    print("Stack after running optimized program:")
    b = Machine(optimized)
    b.run()
    b.dump_stack()

    result = a.data_stack._values == b.data_stack._values
    print("Result: %s" % ("OK" if result else "FAIL"))
    return result

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            cmd = sys.argv[1]
            if cmd == "repl":
                repl()
            elif cmd == "test":
                test_optimizer()
                examples()
            else:
                print("Commands: repl, test")
        else:
            repl()
    except KeyboardInterrupt:
        pass
    except EOFError:
        pass
