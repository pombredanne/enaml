#------------------------------------------------------------------------------
# Copyright (c) 2014, Nucleic Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#------------------------------------------------------------------------------
from .dynamicscope import DynamicScope
from .funchelper import call_func


class DeclarativeFunction(object):
    """ A descriptor which represents a declarative function.

    """
    # XXX move this class to C++
    __slots__ = ('im_func', 'im_class', 'im_key')

    def __init__(self, im_func, im_class, im_key):
        """ Initialize a DeclarativeFunction.

        Parameters
        ----------
        im_func : FunctionType
            The Python function which implements the logic.

        im_class : type
            The declarative class on which this function lives.

        im_key : object
            The scope im_key to lookup the function locals.

        """
        self.im_func = im_func
        self.im_class = im_class
        self.im_key = im_key

    @property
    def _d_func(self):
        return True

    def __repr__(self):
        klass = self.im_class.__name__
        name = self.im_func.__name__
        return '<declarative function %s.%s>' % (klass, name)

    def __get__(self, im_self, ignored):
        if im_self is None:
            return self
        return BoundDeclarativeMethod(
            self.im_func, self.im_class, self.im_key, im_self)


def super_disallowed(*args, **kwargs):
    """ A function which disallows super() in a declarative function.

    """
    msg = ('super() is not allowed in a declarative function, '
           'use SomeClass.some_method(self, ...) instead.')
    raise TypeError(msg)


class BoundDeclarativeMethod(object):
    """ An object which represents a bound declarative method.

    """
    # XXX move this class to C++
    __slots__ = ('im_func', 'im_class', 'im_key', 'im_self')

    def __init__(self, im_func, im_class, im_key, im_self):
        """ Initialize a BoundDeclarativeMethod.

        Parameters
        ----------
        im_func : FunctionType
            The Python function which implements the logic.

        im_class : type
            The declarative class on which this function lives.

        im_key : object
            The scope key to lookup the function locals.

        im_self : Declarative
            The declarative 'self' context for the function.

        """
        self.im_func = im_func
        self.im_class = im_class
        self.im_key = im_key
        self.im_self = im_self

    def __repr__(self):
        im_func = self.im_func
        im_self = self.im_self
        args = (type(im_self).__name__, im_func.__name__, im_self)
        return '<bound declarative method %s.%s of %r>' % args

    def __call__(self, *args, **kwargs):
        im_func = self.im_func
        f_globals = im_func.func_globals
        f_builtins = f_globals['__builtins__']
        im_self = self.im_self
        f_locals = im_self._d_storage.get(self.im_key) or {}
        scope = DynamicScope(im_self, f_locals, f_globals, f_builtins)
        scope['super'] = super_disallowed
        return call_func(im_func, args, kwargs, scope)
