#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# Copyright 2016 Renan Strauss

# PyQuine is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# PyQuine is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with PyQuine.  If not, see <http://www.gnu.org/licenses/>

from collections import Counter
from copy import deepcopy as dc

def is_atom(obj):
	return type(obj) is str and obj.isalpha()

def is_bool(obj):
	return type(obj) is str and obj.isnumeric()

def is_expr(obj):
	return isinstance(obj, Expression)

def is_not(obj):
	return isinstance(obj, Not)

def is_true(s):
	return s == '1'

class Expression(object):

	#
	# A Counter object with
	# each atom occurence
	#
	@property
	def atomscount(self):
	    raise NotImplementedError()

	def delete_atom(self, name, value):
		raise NotImplementedError()

	#
	# Returns True if and only if self
	# is atomic (ie. does not hold 0 or 1)
	@property
	def isatomic(self):
		raise NotImplementedError()

	#
	# Returns a reduced version of self
	#
	def reduced(self):
		raise NotImplementedError()
	
class Not(Expression):
	def __init__(self, expr):
		#if type(expr) is Not and type(expr.expr) is str:
		self._expr = expr

	#
	# A Counter object with
	# each atom occurence
	#
	@property
	def atoms_count(self):
		c = Counter()
		if is_atom(self.expr):
			c[self.expr] += 1
		elif is_expr(self.expr):
			c += self.expr.atoms_count

		return c

	def delete_atom(self, name, value):
		if is_atom(self.expr) and self.expr == name:
			self._expr = '1' if value else '0'
		elif is_expr(self.expr):
			self.expr.delete_atom(name, value)

	@property
	def expr(self):
	    return self._expr

	#
	# Returns True if and only if self
	# is atomic (ie. does not hold 0 or 1)
	@property
	def isatomic(self):
		if is_atom(self.expr):
			return True
		if is_expr(self.expr):
			return self.expr.isatomic
		return False

	#
	# Returns a reduced version of self
	#
	def reduced(self):
		if is_atom(self.expr):
			return self
		elif is_bool(self.expr):
			return '1' if self.expr == '0' else '0'
		elif is_not(self.expr) or is_expr(self.expr):
			return Not(self.expr.reduced())

		return None

	def __eq__(self, other):
		if is_not(other):
			return self._expr == other.expr
		return False

	def __str__(self):
		return '!%s' % self._expr

class BinaryExpr(Expression):
	def __init__(self, lexpr, op, rexpr):
		self._rexpr = rexpr
		self._op = op
		self._lexpr = lexpr

	def delete_atom(self, name, value):
		if is_atom(self.lexpr) and self.lexpr == name:
			self._lexpr = '1' if value else '0'
		elif is_expr(self._lexpr):
			self.lexpr.delete_atom(name, value)

		if is_atom(self.rexpr) and self.rexpr == name:
			self._rexpr = '1' if value else '0'
		elif is_expr(self.rexpr):
			self.rexpr.delete_atom(name, value)

	# Returns a reduced version of self,
	# by simplification if any of the values
	# in self is fixed (ie is 0 or 1)
	def reduced(self):
		# That simple, yeah..
		# Notice: => operator was added because
		# it's not needed to go for another run
		# with expr => expr I guess
		if self.op in ('<=>', '=>'):
			if (str(self.lexpr) == str(self.rexpr)) or \
			   (is_bool(self.lexpr) and is_bool(self.rexpr) and self.lexpr == self.rexpr):
				return '1'

		if self.isatomic:
			return self

		if self.op == '=>':
			#if is_not(self.lexpr) and is_not(self.rexpr):
			#	if type(self.lexpr.expr) == type(self.rexpr.expr):
			#		return '1' if self.lexpr.expr == self.rexpr.expr else '0'
			if is_not(self.lexpr):
				if type(self.lexpr.expr) == type(self.rexpr) and self.lexpr.expr == self.rexpr:
					return self.lexpr.expr
			elif is_not(self.rexpr):
				if type(self.lexpr) == type(self.rexpr.expr) and self.rexpr.expr == self.lexpr:
					return Not(self.rexpr)

		if is_bool(self.lexpr):
			if self.op == '^':
				if is_true(self.lexpr):
					return self.rexpr
				return '0'
			elif self.op == 'v':
				if is_true(self.lexpr):
					return '1'
				return self.rexpr
			elif self.op == '=>':
				if is_true(self.lexpr):
					return self.rexpr
				return '1'
			elif self.op == '<=>':
				if is_true(self.lexpr):
					return self.rexpr
				return Not(self.rexpr)
		
		if is_bool(self.rexpr):
			if self.op == '^':
				if is_true(self.rexpr):
					return self.lexpr
				return '0'
			elif self.op == 'v':
				if is_true(self.rexpr):
					return '1'
				return self.lexpr
			elif self.op == '=>':
				if is_true(self.rexpr):
					return '1'
				return Not(self.lexpr)
			elif self.op == '<=>':
				if is_true(self.rexpr):
					return self.lexpr
				return Not(self.lexpr)

		if is_expr(self.lexpr) and is_expr(self.rexpr):
			return BinaryExpr(self.lexpr.reduced(), self.op, self.rexpr.reduced())
		elif is_expr(self.lexpr):
			return BinaryExpr(self.lexpr.reduced(), self.op, self.rexpr)
		elif is_expr(self.rexpr):
			return BinaryExpr(self.lexpr, self.op, self.rexpr.reduced())

		return self

	@property
	def isatomic(self):
		# Not so beautiful but does the trick
		if '0' in str(self) or '1' in str(self):
			return False
		return True

	@property
	def lexpr(self):
	    return self._lexpr
	
	@property
	def op(self):
	    return self._op
	
	@property
	def rexpr(self):
	    return self._rexpr

	@property
	def atoms_count(self):
		c = Counter()
		for expr in (self._rexpr, self._lexpr):
			if is_atom(expr):
				c[expr] += 1
			elif is_expr(expr):
				c += expr.atoms_count

		return c
	
	@classmethod
	def fromstring(klazz, string):
		# NYI
		return None

	def __eq__(self, other):
		if is_expr(other):
			return other.lexpr == self.lexpr and other.op == self.op \
			   and other.rexpr == self.rexpr and other.atoms_count == self.atoms_count
		return False

	def __str__(self):
		return '(%s %s %s)' % (self._lexpr, self._op, self._rexpr)

#
# Actually gets the job done.
# Yields two values for each expansion
# and prints the process.
#
def quineprove(expr, indent_lvl = 0):
	def _generate_indent(lvl):
		indents = []
		for i in range(lvl):
			indents.append('\t')
		return ''.join(indents)
	def _output(msg):
		print('%s%s' % (_generate_indent(indent_lvl), msg))

	# First of all, determine which atom to replace
	# TODO: find a way to determine the best atom to replace
	#       when all atoms have the same frequency
	to_replace = expr.atoms_count.most_common()[0][0]

	_output('[CHECKING] %s' % expr)

	# Replace atom to_replace with 1 then with 0
	for val in (True, False):
		e = dc(expr)
		e.delete_atom(to_replace, val)

		_output('[EXPANDING] %s' % e)

		e = e.reduced()
		while type(e) is not str:
			_output('%s' % e)
			if is_expr(e) and e.isatomic and e.reduced() == e:
				l, r = quineprove(dc(e), indent_lvl + 1)
				if is_bool(l) and is_bool(r):
					e = '1' if is_true(l) and is_true(r) else '0'
					# TODO: handle not-decidable cases for a more understandable output
				break

			e = e.reduced()

		_output('[DONE] %s' % e)
		yield e

# Some examples (tautologies)
examples = (
	BinaryExpr(BinaryExpr('p', '=>', 'q'), '<=>', BinaryExpr(Not('p'), 'v', 'q')),
	BinaryExpr(BinaryExpr(Not('p'), '^', Not('q')), '=>', Not(BinaryExpr('p', 'v', 'q'))),
	BinaryExpr(BinaryExpr('p', '=>', 'q'), 'v', BinaryExpr('q', '=>', 'p')),
	BinaryExpr(BinaryExpr(BinaryExpr('p' , '=>', 'q'), '=>', 'r'), '<=>', BinaryExpr(Not(BinaryExpr(Not('p'), 'v', 'q')), 'v', 'r')),
	BinaryExpr(BinaryExpr('p', '=>', 'r'), '=>', BinaryExpr(BinaryExpr('q', '=>', 'r'), '=>', BinaryExpr(BinaryExpr('p', 'v', 'q'), '=>', 'r'))),
	BinaryExpr(BinaryExpr(BinaryExpr('a', '=>', 'b'), '^', 'a'), '=>', 'b'),
)

for expr in examples:
	print('\n==================================================================\n')
	l, r = quineprove(expr)
	print('[RESULTS] %s | %s' % (l, r))
