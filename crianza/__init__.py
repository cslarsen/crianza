from instructions import (Instruction, lookup)

from errors import (
    CompileError,
    MachineError,
    ParseError,
)

from vm import (
    Instruction,
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
