from crianza.compiler import (check, compile)
from crianza.errors import CompileError, MachineError, ParseError
from crianza.instructions import lookup
from crianza.optimizer import constant_fold, optimized
from crianza.parser import (parse, parse_stream)
from crianza.repl import repl, print_code
from crianza.stack import Stack
from crianza.interpreter import (
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

__author__ = "Christian Stigen Larsen"
__copyright__ = "Copyright (C) 2015 Christian Stigen Larsen"
__email__ = "csl@csl.name"
__license__ = "BSD 3-Clause"
__version__ = "0.1.9"

__all__ = [
    "CompileError",
    "Instruction",
    "Machine",
    "MachineError",
    "ParseError",
    "Stack",
    "check",
    "code_to_string",
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
    "print_code",
    "repl",
]
