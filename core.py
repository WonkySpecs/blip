class Atom:
    def __init__(self, string):
        self.string = string

    def __eq__(self, other):
        return type(other) == Atom and self.string == other.string or type(other) == SExpr and other.is_atom and other.value == self

    def __str__(self):
        return self.string

    def __hash__(self):
        return hash(self.string)

Atom.true = Atom("t")
Atom.false = Atom("f")

class SExpr:
    def __init__(self, atom=None, elements=None):
        # "is not None" necessary as an empty list is valid for elements
        assert atom or elements is not None
        if atom:
            self.value = atom
        else:
            self.value = elements

    @property
    def is_atom(self):
        return type(self.value) == Atom

    def __str__(self):
        if self.is_atom:
            return str(self.value)
        else:
            return f"({' '.join((str(sub) for sub in self.value))})"


class Parser:
    def init(self, s):
        self.cur = 0
        self.s = s

    def _is_done(self):
        return self.cur >= len(self.s)

    def _is_atom_char(self):
        c = self.s[self.cur]
        return not c.isspace() and c not in ['(', ')']

    def _parse_atom(self):
        start = self.cur
        while not self._is_done() and self._is_atom_char():
            self.cur += 1
        return SExpr(atom=Atom(self.s[start : self.cur]))

    def _parse_list(self):
        exprs = []
        while not self._is_done():
            cur = self.s[self.cur]
            if cur == ' ':
                self.cur += 1
                pass
            elif cur == ')':
                self.cur += 1
                return SExpr(elements=exprs)
            elif cur == '(':
                self.cur += 1
                exprs.append(self._parse_list())
            else:
                exprs.append(self._parse_atom())
        self.err(f"Unclosed expression")

    def run(self, s):
        self.init(s)
        exprs = []
        while not self._is_done():
            cur = s[self.cur]
            if cur == ' ':
                pass
            elif cur == ')': 
                self.err("Unexpected ')'")
            elif cur == '(':
                self.cur += 1
                exprs.append(self._parse_list())
            else:
                exprs.append(self._parse_atom())
            self.cur += 1

        return exprs

    def err(self, msg):
        raise Exception(f'Error parsing "{self.s}" at {self.cur}: {msg}')

def str_exprs(exprs):
    return [str(e) for e in exprs]

class VM:
    def __init__(self):
        self._core_fns = {
            Atom(f.__name__): f for f in [
                self.atom,
                self.eq,
                self.first,
                self.rest,
                self.cons]
        }
        self._env = [(a, f) for a, f in self._core_fns.items()
                ] + [(Atom.true, Atom.true), (Atom.false, Atom.false)]
        self.parser = Parser()

    def read(self, s):
        return self.parser.run(s)

    def eval(self, expr):
        if expr.is_atom:
            return self._get(expr.value)
        # Empty list evaluates to itself - not sure how correct this is
        elif len(expr.value) == 0:
            return expr
        elif self.first(expr).is_atom:
            atom_fn = self.first(expr).value
            if atom_fn.string == "quote":
                return self.first(self.rest(expr))
            elif atom_fn in self._core_fns:
                to_apply = self._core_fns[atom_fn]
                # -1 for self
                num_args = to_apply.__code__.co_argcount - 1
                args = expr.value[1:]
                assert num_args == len(args), f"Builtin '{atom_fn.string}' requires {num_args} args, {len(args)} given"
                evalled = [self.eval(a) for a in args]
                return to_apply(*evalled)
            elif atom_fn.string == "cond":
                return self.cond(self.rest(expr))
            else:
                to_apply = self._get(atom_fn)
                args = self.rest(expr)
                return self.eval(self.cons(to_apply, args))
        else:
            caar = self.first(self.first(expr))
            if caar.is_atom:
                if caar.value.string == "fn":
                    defs = self.rest(self.first(expr))
                    args = self.first(defs).value
                    to_eval = self.first(self.rest(defs))
                    params = self.rest(expr).value

                    assert len(args) == len(params), f"Lambda function '{self.first(self.first(expr))}' requires {len(args)} args, {len(params)} were given"

                    for a, p in zip(args, params):
                        self._env.append((a, self.eval(p)))
                    res = self.eval(to_eval)
                    for _ in params:
                        self._env.pop()
                    return res
                elif caar.value.string == "def":
                    defs = self.rest(self.first(expr))
                    label = self.first(defs)
                    to_append = self.first(self.rest(defs))
                    new_expr = self.cons(to_append, self.rest(expr))
                    self._env.append((label, to_append))
                    res = self.eval(new_expr)
                    self._env.pop()
                    return res


    def print(self, o):
        print(str(o))

    def _get(self, symbol):
        for label, obj in reversed(self._env):
            if label == symbol:
                return obj
        raise Exception(f"Unable to resolve atom '{symbol}'")

    def atom(self, expr):
        return Atom.true if expr.is_atom else Atom.false

    def eq(self, a, b):
        if a.is_atom and b.is_atom:
            return Atom.true if a.value == b.value else Atom.false
        assert False, "eq can only be applied to atoms"

    def first(self, expr):
        assert not expr.is_atom, "first cannot be applied to atoms"
        return expr.value[0]

    def rest(self, expr):
        assert not expr.is_atom, "rest cannot be applied to atoms"
        return SExpr(elements=expr.value[1:])

    def cons(self, a, b):
        assert not b.is_atom, "Second argument to cons cannot be an atom"
        return SExpr(elements=[a, *b.value])

    def quote(self, expr):
        return expr

    def cond(self, expr):
        assert not expr.is_atom and len(expr.value) % 2 == 0, "cond requires an even number of args"
        pairs = expr.value
        for i in range(0, len(pairs), 2):
            if self.eval(pairs[i]) == Atom.true:
                return self.eval(pairs[i + 1])
