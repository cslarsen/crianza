from vm import (
    CompilationError,
    Instruction,
    Machine,
    MachineError,
    ParserError,
    Stack,
    check,
    compile,
    constant_fold,
    eval,
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
