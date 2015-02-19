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
    isbinary,
    isbool,
    isconstant,
    isnumber,
    isstring,
    lookup,
    optimize,
    parse,
    repl,
)

__version__ = "0.0.1"
