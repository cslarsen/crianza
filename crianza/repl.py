import sys

from compiler import compile, is_embedded_push, get_embedded_push_value
from errors import ParseError, MachineError, CompileError
from parser import parse
from interpreter import isstring, Machine


def print_code(vm, out=sys.stdout, ops_per_line=8, registers=True):
    """Prints code and state for VM."""
    if registers:
        out.write("IP: %d\n" % vm.instruction_pointer)
        out.write("DS: %s\n" % str(vm.stack))
        out.write("RS: %s\n" % str(vm.return_stack))

    def to_str(op):
        if is_embedded_push(op):
            op = get_embedded_push_value(op)

        if isstring(op):
            return '"%s"' % repr(op)[1:-1]
        elif callable(op):
            return vm.lookup(op)
        else:
            return str(op)

    for addr, op in enumerate(vm.code):
        if (addr % ops_per_line) == 0 and (addr==0 or (addr+1) < len(vm.code)):
            if addr > 0:
                out.write("\n")
            out.write("%0*d  " % (max(4, len(str(len(vm.code)))), addr))
        out.write("%s " % to_str(op))
    out.write("\n")

def repl(optimize=True, persist=True):
    """Starts a simple REPL for this machine.

    Args:
        optimize: Controls whether to run inputted code through the
        optimizer.

        persist: If True, the machine is not deleted after each line.
    """
    print("Extra commands for the REPL:")
    print(".code    - print code")
    print(".raw     - print raw code")
    print(".quit    - exit immediately")
    print(".reset   - reset machine (IP and stacks)")
    print(".restart - create a clean, new machine")
    print(".clear   - same as .restart")
    print(".stack   - print data stack")
    print("")

    machine = Machine([])

    def match(s, *args):
        return any(map(lambda arg: s.strip()==arg, args))

    while True:
        try:
            source = raw_input("> ").strip()

            if source[0] == "." and len(source) > 1:
                if match(source, ".quit"):
                    return
                elif match(source, ".code"):
                    print_code(machine)
                elif match(source, ".raw"):
                    print(machine.code)
                elif match(source, ".reset"):
                    machine.reset()
                elif match(source, ".restart", ".clear"):
                    machine = Machine([])
                elif match(source, ".stack"):
                    print(machine.stack)
                else:
                    raise ParseError("Unknown command: %s" % source)
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
