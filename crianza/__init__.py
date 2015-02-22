from instructions import (Instruction, lookup)

from errors import (
    CompileError,
    MachineError,
    ParseError,
)

from vm import (
    Machine,
    Stack,
    constant_fold,
    eval,
    execute,
    isbinary,
    isbool,
    isconstant,
    isnumber,
    isstring,
    optimized,
    repl,
)

from parser import (parse, parse_stream)
from compiler import (check, compile)

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
