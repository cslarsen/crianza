class MachineError(Exception):
    """A VM runtime error."""
    pass

class ParseError(Exception):
    """An error occurring during parsing."""
    pass

class CompileError(Exception):
    """An error ocurring during compilation."""
    pass
