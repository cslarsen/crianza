import sys

from compiler import compile
from errors import ParseError, MachineError, CompileError
from parser import parse
from interpreter import isstring, Machine


def repl(optimize=True, persist=True):
    """Starts a simple REPL for this machine.

    Args:
        optimize: Controls whether to run inputted code through the
        optimizer.

        persist: If True, the machine is not deleted after each line.
    """

    def print_code(vm, ops_per_line=8):
        """Prints code and state for VM."""
        print("IP: %d" % vm.instruction_pointer)
        print("DS: %s" % str(vm.stack))
        print("RS: %s" % str(vm.return_stack))

        for addr, op in enumerate(vm.code):
            if (addr % ops_per_line) == 0 and (addr+1) < len(vm.code):
                if addr > 0:
                    sys.stdout.write("\n")
                sys.stdout.write("%0*d  " % (max(4, len(str(len(vm.code)))), addr))
            value = str(op)
            if isstring(op):
                value = repr(op)[1:-1]
            sys.stdout.write("%s " % value)
        sys.stdout.write("\n")

    print("Extra commands for the REPL:")
    print(".code    - print code")
    print(".quit    - exit immediately")
    print(".reset   - reset machine (IP and stacks)")
    print(".restart - create a clean, new machine")
    print("")

    machine = Machine([])

    while True:
        try:
            source = raw_input("> ").strip()

            if source == ".quit":
                return
            elif source == ".code":
                print_code(machine)
                continue
            elif source == ".reset":
                machine.reset()
                continue
            elif source == ".restart":
                machine = Machine([])
                continue

            code = compile(parse(source), silent=False, optimize=optimize)

            if not persist:
                machine.reset()

            machine.code += code
            machine.run()
        except EOFError:
            return
        except KeyboardInterrupt:
            return
        except ParseError, e:
            print("Parser error: %s" % e)
        except MachineError, e:
            print("Machine error: %s" % e)
        except CompileError, e:
            print("Compile error: %s" % e)
