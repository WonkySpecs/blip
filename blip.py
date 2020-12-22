import core
import sys

def file_gen(filename):
    with open(filename, 'r') as f:
        for line in f:
            yield line

def interp_gen():
    while True:
        s = input(": ")
        if s == "exit":
            break
        yield s
    print("Bye ^_^")

if __name__ == "__main__":
    vm = core.VM()
    if len(sys.argv) == 1:
        gen = interp_gen()
    else:
        filename = sys.argv[1]
        gen = file_gen(filename)

    for line in gen:
        try:
            exprs = vm.read(line)
            for e in exprs:
                vm.print(vm.eval(e))
        except Exception as e:
            print(f"Error: {e}")


