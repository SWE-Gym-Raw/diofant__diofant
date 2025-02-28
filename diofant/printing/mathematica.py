"""Mathematica code printer."""

import types

from ..sets import Reals
from .codeprinter import CodePrinter
from .precedence import PRECEDENCE, precedence
from .str import StrPrinter


# Used in MCodePrinter._print_Function(self)
known_functions = {
    'log': [(lambda x: True, 'Log')],
    'sin': [(lambda x: True, 'Sin')],
    'cos': [(lambda x: True, 'Cos')],
    'tan': [(lambda x: True, 'Tan')],
    'cot': [(lambda x: True, 'Cot')],
    'asin': [(lambda x: True, 'ArcSin')],
    'acos': [(lambda x: True, 'ArcCos')],
    'atan': [(lambda x: True, 'ArcTan')],
    'acot': [(lambda x: True, 'ArcCot')],
    'sinh': [(lambda x: True, 'Sinh')],
    'cosh': [(lambda x: True, 'Cosh')],
    'tanh': [(lambda x: True, 'Tanh')],
    'coth': [(lambda x: True, 'Coth')],
    'asinh': [(lambda x: True, 'ArcSinh')],
    'acosh': [(lambda x: True, 'ArcCosh')],
    'atanh': [(lambda x: True, 'ArcTanh')],
    'acoth': [(lambda x: True, 'ArcCoth')],
    'sech': [(lambda x: True, 'Sech')],
    'csch': [(lambda x: True, 'Csch')],
    'sign': [(lambda x: True, 'Sign')],
    'meijerg': [(lambda *x: True, 'MeijerG')],
    'hyper': [(lambda *x: True, 'HypergeometricPFQ')],
    'binomial': [(lambda n, k: True, 'Binomial')],
    'erf': [(lambda x: True, 'Erf')],
    'erfi': [(lambda x: True, 'Erfi')],
    'erfc': [(lambda x: True, 'Erfc')],
    'conjugate': [(lambda x: True, 'Conjugate')],
    're': [(lambda x: True, 'Re')],
    'im': [(lambda x: True, 'Im')],
    'polygamma': [(lambda n, x: True, 'PolyGamma')],
    'Max': [(lambda *x: True, 'Max')],
    'Min': [(lambda *x: True, 'Min')],
    'factorial': [(lambda x: True, 'Factorial')],
    'factorial2': [(lambda *x: True, 'Factorial2')],
    'RisingFactorial': [(lambda x, k: True, 'Pochhammer')],
    'gamma': [(lambda x: True, 'Gamma')],
    'Heaviside': [(lambda x: True, 'UnitStep')],
    'fibonacci': [(lambda x: True, 'Fibonacci')],
    'polylog': [(lambda x, y: True, 'PolyLog')],
    'loggamma': [(lambda x: True, 'LogGamma')],
    'uppergamma': [(lambda s, x: True, 'Gamma')],
    'floor': [(lambda x: True, 'Floor')],
    'ceiling': [(lambda x: True, 'Ceiling')],
    'arg': [(lambda x: True, 'Arg')],
    'Ei': [(lambda x: True, 'ExpIntegralEi')],
    'expint': [(lambda n, x: True, 'ExpIntegralE')],
    'Si': [(lambda x: True, 'SinIntegral')],
    'Ci': [(lambda x: True, 'CosIntegral')],
    'lerchphi': [(lambda z, s, a: True, 'HurwitzLerchPhi')],
    'airyai': [(lambda x: True, 'AiryAi')],
    'airyaiprime': [(lambda x: True, 'AiryAiPrime')],
    'airybi': [(lambda x: True, 'AiryBi')],
    'airybiprime': [(lambda x: True, 'AiryBiPrime')],
    'li': [(lambda x: True, 'LogIntegral')],
}


class MCodePrinter(CodePrinter):
    """A printer to convert python expressions to
    strings of the Wolfram's Mathematica code.

    """

    printmethod = '_mcode'

    _default_settings = {
        'order': None,
        'full_prec': 'auto',
        'precision': 15,
        'user_functions': {},
        'human': True,
    }

    _number_symbols = set()
    _not_supported = set()

    def __init__(self, settings={}):
        """Register function mappings supplied by user."""
        CodePrinter.__init__(self, settings)
        self.known_functions = dict(known_functions)
        userfuncs = settings.get('user_functions', {})
        for k, v in userfuncs.items():
            if not isinstance(v, list):
                userfuncs[k] = [(lambda *x: True, str(v))]
            else:
                v = v[0]
                if (isinstance(v, (list, tuple)) and len(v) == 2 and
                        isinstance(v[0], types.FunctionType)):
                    userfuncs[k] = [(v[0], str(v[1]))]
                else:
                    raise ValueError('bad user_functions')
            self.known_functions.update(userfuncs)

    doprint = StrPrinter.doprint

    def _print_Pow(self, expr):
        PREC = precedence(expr)
        return f'{self.parenthesize(expr.base, PREC)}^{self.parenthesize(expr.exp, PREC)}'

    def _print_Mul(self, expr):
        PREC = precedence(expr)
        c, nc = expr.args_cnc()
        res = super()._print_Mul(expr.func(*c))
        if nc:
            res += '*'
            res += '**'.join(self.parenthesize(a, PREC) for a in nc)
        return res

    def _print_Pi(self, expr):
        return 'Pi'

    def _print_Infinity(self, expr):
        return 'Infinity'

    def _print_NegativeInfinity(self, expr):
        return '-Infinity'

    def _print_list(self, expr):
        return '{' + ', '.join(self.doprint(a) for a in expr) + '}'
    _print_tuple = _print_list
    _print_Tuple = _print_list
    _print_ExprCondPair = _print_list

    def _print_Function(self, expr):
        fname = expr.func.__name__
        if fname in self.known_functions:
            cond, mfunc = self.known_functions[fname][0]
            if cond(*expr.args):
                return f"{mfunc}[{self.stringify(expr.args, ', ')}]"
        return fname + f"[{self.stringify(expr.args, ', ')}]"
    _print_MinMaxBase = _print_Function

    def _print_lowergamma(self, expr):
        return f"{self.parenthesize(expr.rewrite('uppergamma'), PRECEDENCE['Add'])}"

    def _print_Li(self, expr):
        return f"{self.parenthesize(expr.rewrite('li'), PRECEDENCE['Add'])}"

    def _print_zeta(self, expr):
        if len(expr.args) == 1:
            return f'Zeta[{self.doprint(expr.args[0])}]'
        return f"HurwitzZeta[{self.stringify(expr.args, ', ')}]"

    def _print_atan2(self, expr):
        return f"ArcTan[{', '.join(map(self.doprint, reversed(expr.args)))}]"

    def _print_Piecewise(self, expr):
        return expr.func.__name__ + f"[{{{self.stringify(expr.args, ', ')}}}]"

    def _print_BooleanTrue(self, expr):
        return 'True'

    def _print_BooleanFalse(self, expr):
        return 'False'

    def _print_Derivative(self, expr):
        return f"Hold[D[{self.doprint(expr.expr)}, {', '.join(self.doprint(a) for a in expr.variables)}]]"

    def _print_Integral(self, expr):
        if len(expr.variables) == 1 and not expr.limits[0][1:]:
            args = [expr.args[0], expr.variables[0]]
        else:
            args = expr.args
        return 'Hold[Integrate[' + ', '.join(self.doprint(a) for a in args) + ']]'

    def _print_Limit(self, expr):
        direction = expr.args[-1]
        if direction == Reals:
            direction = 'Reals'
        else:
            direction = self.doprint(direction)
        e, x, x0 = (self.doprint(a) for a in expr.args[:-1])
        return f'Hold[Limit[{e}, {x} -> {x0}, Direction -> {direction}]]'

    def _print_Sum(self, expr):
        return f'Hold[{expr.__class__.__name__}[' + ', '.join(self.doprint(a) for a in expr.args) + ']]'
    _print_Product = _print_Sum

    def _print_MatrixBase(self, expr):
        return self.doprint(expr.tolist())

    _print_Matrix = \
        _print_SparseMatrix = \
        _print_MutableSparseMatrix = \
        _print_ImmutableSparseMatrix = \
        _print_DenseMatrix = \
        _print_MutableDenseMatrix = \
        _print_ImmutableMatrix = \
        _print_ImmutableDenseMatrix = \
        _print_MatrixBase

    def _print_Relational(self, expr):
        PREC = precedence(expr)
        return f'{self.parenthesize(expr.lhs, PREC)} {expr.rel_op} {self.parenthesize(expr.rhs, PREC)}'

    def _print_RootOf(self, expr):
        from ..core import Symbol

        return f"Root[{self.doprint(expr.expr.subs({expr.poly.gen: Symbol('#')}))} &, {self.doprint(expr.index + 1)}]"

    def _print_Lambda(self, obj):
        return f'Function[{self.doprint(obj.variables)}, {self.doprint(obj.expr)}]'

    def _print_RootSum(self, expr):
        from ..core import Lambda
        p, f = expr.poly, expr.fun
        return f'RootSum[{self.doprint(Lambda(p.gens, p.as_expr()))}, {self.doprint(f)}]'

    def _print_AlgebraicElement(self, expr):
        coeffs = expr.rep.all_coeffs()
        return f'AlgebraicNumber[{self.doprint(expr.parent.ext)}, {self.doprint(coeffs)}]'

    def _print_Dummy(self, expr):
        return f'{expr.name}{expr.dummy_index}'

    def _print_IntegralTransform(self, expr):
        return (f'Hold[{expr.func}[{expr.function}, '
                f'{expr.function_variable}, {expr.transform_variable}, '
                'GenerateConditions->True]]')


def mathematica_code(expr, **settings):
    r"""Converts an expr to a string of the Wolfram Mathematica code

    Examples
    ========

    >>> mathematica_code(sin(x).series(x).removeO())
    '(1/120)*x^5 - 1/6*x^3 + x'

    """
    return MCodePrinter(settings).doprint(expr)
