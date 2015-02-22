from errors import MachineError

class Stack(object):
    """A stack of values."""
    def __init__(self):
        self._values = []

    def pop(self):
        if len(self._values) == 0:
            raise MachineError("Stack underflow")
        return self._values.pop()

    def push(self, value):
        self._values.append(value)

    @property
    def top(self):
        return None if len(self._values) == 0 else self._values[-1]

    def __str__(self):
        return str(self._values)

    def __repr__(self):
        return "<Stack: values=%s>" % self._values

    def __len__(self):
        return len(self._values)

    def __getitem__(self, key):
        return self._values[key]
