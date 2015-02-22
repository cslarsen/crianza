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
    check,
    compile,
    constant_fold,
    eval,
    execute,
    isbinary,
    isbool,
    isconstant,
    isnumber,
    isstring,
    optimized,
    parse,
    parse_stream,
    repl,
)

__version__ = "0.0.1"
