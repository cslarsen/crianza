from compiler import (check, compile)
from errors import CompileError, MachineError, ParseError
from instructions import lookup
from optimizer import constant_fold, optimized
from parser import (parse, parse_stream)
from repl import repl
from stack import Stack
from interpreter import (
    Machine,
    code_to_string,
    eval,
    execute,
    isbinary,
    isbool,
    isconstant,
    isnumber,
    isstring,
)

__version__ = "0.1"

__all__ = [
    "CompileError",
    "Instruction",
    "Instruction",
    "Machine",
    "MachineError",
    "ParseError",
    "Stack",
    "check",
    "code_to_string,"
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
