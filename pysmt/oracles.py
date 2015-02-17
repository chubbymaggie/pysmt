#
# This file is part of pySMT.
#
#   Copyright 2015 Andrea Micheli and Marco Gario
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
"""This module provides classes used to analyze and determine
properties of formulae.

 * QuantifierOracle says whether a formula is quantifier free
 * TheoryOracle says which logic is used in the formula.
"""

import pysmt.walkers as walkers
import pysmt.operators as op
import pysmt.shortcuts

from pysmt.logics import Logic, get_closer_pysmt_logic


class QuantifierOracle(walkers.DagWalker):
    def __init__(self, env=None):
        walkers.DagWalker.__init__(self, env=env)

        # Clear the mapping function
        self.functions.clear()

        # Propagate truth value, and force False when a Quantifier
        # is found.
        for elem in op.ALL_TYPES:
            if elem in [op.FORALL, op.EXISTS]:
                self.functions[elem] = self.walk_false
            else:
                self.functions[elem] = self.walk_all

        # Check that no operator in undefined
        assert self.is_complete(verbose=True)

    def is_qf(self, formula):
        """ Returns whether formula is Quantifier Free. """
        return self.walk(formula)


# EOC QuantifierOracle


class TheoryOracle(walkers.DagWalker):
    def __init__(self, env=None):
        walkers.DagWalker.__init__(self, env=env)

        self.functions[op.AND] = self.walk_combine
        self.functions[op.OR] = self.walk_combine
        self.functions[op.NOT] = self.walk_combine
        self.functions[op.IMPLIES] = self.walk_combine
        self.functions[op.IFF] = self.walk_combine
        self.functions[op.LE] = self.walk_combine
        self.functions[op.LT] = self.walk_combine
        self.functions[op.FORALL] = self.walk_combine
        self.functions[op.EXISTS] = self.walk_combine
        self.functions[op.MINUS] = self.walk_combine
        self.functions[op.ITE] = self.walk_combine

        self.functions[op.REAL_CONSTANT] = self.walk_constant
        self.functions[op.SYMBOL] = self.walk_symbol
        self.functions[op.FUNCTION] = self.walk_function
        self.functions[op.BOOL_CONSTANT] = self.walk_constant
        self.functions[op.INT_CONSTANT] = self.walk_constant
        self.functions[op.TOREAL] = self.walk_lira
        self.functions[op.TIMES] = self.walk_times
        self.functions[op.PLUS] = self.walk_plus
        self.functions[op.EQUALS] = self.walk_equals

    def walk_combine(self, formula, args):
        """Combines the current theory value of the children"""
        theory_out = args[0]
        for t in args[1:]:
            theory_out = theory_out | t

        return theory_out

    def walk_constant(self, formula, args):
        """Returns a new theory object with the type of the constant."""
        if formula.is_real_constant():
            theory_out = Logic(name="", description="",
                               real_arithmetic=True, real_difference=True,
                               linear=True)
        elif formula.is_int_constant():
            theory_out = Logic(name="", description="",
                               integer_arithmetic=True, integer_difference=True,
                               linear=True)
        else:
            assert formula.is_bool_constant()
            theory_out = Logic(name="", description="")

        return theory_out

    def walk_symbol(self, formula, args):
        """Returns a new theory object with the type of the symbol."""
        f_type = formula.symbol_type()
        if f_type.is_real_type():
            theory_out = Logic(name="", description="",
                               real_arithmetic=True, real_difference=True,
                               linear=True)
        elif f_type.is_int_type():
            theory_out = Logic(name="", description="",
                               integer_arithmetic=True, integer_difference=True,
                               linear=True)
        elif f_type.is_bool_type():
            theory_out = Logic(name="", description="")
        else:
            assert f_type.is_function_type()
            theory_out = Logic(name="", description="",
                               uninterpreted=True)

        return theory_out

    def walk_function(self, formula, args):
        """Extends the Theory with UF."""
        if len(args) > 0:
            theory_out = args[0]
            for t in args[1:]:
                theory_out = theory_out | t
        else:
            theory_out = Logic(name="",description="")

        theory_out.uninterpreted = True
        return theory_out


    def walk_lira(self, formula, args):
        """Extends the Theory with LIRA."""
        theory_out = args[0]
        theory_out = theory_out.set_lira()
        return theory_out

    def walk_times(self, formula, args):
        """Extends the Theory with Non-Linear, if needed."""
        theory_out = args[0]
        for t in args[1:]:
            theory_out = theory_out | t
        # if Left and Right children are symbolic
        #    theory_out = theory_out.set_non_linear()
        theory_out = theory_out.set_difference_logic(False)
        return theory_out

    def walk_plus(self, formula, args):
        theory_out = args[0]
        for t in args[1:]:
            theory_out = theory_out | t
        theory_out = theory_out.set_difference_logic()
        return theory_out

    def walk_equals(self, formula, args):
        # TODO: Does EQUAL need a special treatment?
        # We consider EUF as UF, shall we split the two concepts?
        return self.walk_combine(formula, args)

    def get_theory(self, formula):
        """Returns the thoery for the formula."""
        return self.walk(formula)


# EOC TheoryOracle


def get_logic(formula):
    env = pysmt.shortcuts.get_env()
    # Get Quantifier Information
    qf = env.qfo.is_qf(formula)
    theory = env.theoryo.get_theory(formula)
    theory.quantifier_free = qf
    # Return a logic supported by PySMT that is close to the one computed
    return get_closer_pysmt_logic(theory)