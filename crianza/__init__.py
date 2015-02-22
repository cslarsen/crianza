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
    lookup,
    optimized,
    parse,
    parse_stream,
    repl,
)

__version__ = "0.0.1"
