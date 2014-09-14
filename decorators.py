#! /usr/bin/python
#
# 

from functools import update_wrapper

def decorator(func):
    return lambda f: update_wrapper(func(f), f)
decorator = decorator(decorator)

memotables = {}

@decorator
def memoid(f): 
    """ memoize a function, based on the id()-s of its inputs
    not on their values. Only use on functions which neglect
    the value of their arguments"""
    memo = memotables[f.__name__] = {} #initialize memo for this function
    def f2(*args):
        idargs = tuple(map(id, args))
        try:
            result = memo[idargs]
        except KeyError:
            memo[idargs] = f(*args)
            result = memo[idargs]
        return result
    return f2
