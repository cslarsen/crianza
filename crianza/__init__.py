from compiler import (check, compile)
from errors import CompileError, MachineError, ParseError
from instructions import (Instruction, lookup)
from optimizer import constant_fold, optimized
from parser import (parse, parse_stream)
from repl import repl
from vm import (
    Machine,
    Stack,
    eval,
    execute,
    isbinary,
    isbool,
    isconstant,
    isnumber,
    isstring,
    optimized,
)

__version__ = "0.0.1"

__all__ = [
    "CompileError",
    "Instruction",
    "Instruction",
    "Machine",
    "MachineError",
    "ParseError",
    "Stack",
    "check",
    "compile",
    "constant_fold",
    "eval",
    "execute",
    "isbinary",
    "isbool",
    "isconstant",
    "isnumber",
    "isstring",
    "lookup",
    "optimized",
    "parse",
    "parse_stream",
    "repl",
]
