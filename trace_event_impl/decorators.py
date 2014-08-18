# Copyright 2011 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import contextlib
import inspect
import time
import functools

import log

@contextlib.contextmanager
def trace(name, **kwargs):
  start = time.time()
  log.add_trace_event("B", start, category, name, kwargs)
  try:
    yield
  finally:
    end = time.time()
    log.add_trace_event("E", end, category, name, kwargs)

def traced(*args):
  def get_wrapper(func):
    if inspect.isgeneratorfunction(func):
      raise Exception("Can not trace generators.")

    category = "python"

    arg_spec = inspect.getargspec(func)
    is_method = arg_spec.args and arg_spec.args[0] == "self"

    def arg_spec_tuple(name):
      arg_index = arg_spec.args.index(name)
      default_index = arg_index + len(arg_spec.defaults) - len(arg_spec.args)
      if default_index >= 0:
        default = arg_spec.defaults[default_index]
      else:
        default = None
      return (name, arg_index, default)

    args_to_log = map(arg_spec_tuple, arg_names)

    @functools.wraps(func)
    def traced_function(*args, **kwargs):
      # Everything outside traced_function is done at decoration-time.
      # Everything inside traced_function is done at run-time and must be fast.
      if not log._enabled:  # This check must be at run-time.
        return func(*args, **kwargs)

      def get_arg_value(name, index, default):
        if name in kwargs:
          return kwargs[name]
        elif index and index < len(args):
          return args[index]
        else:
          return default

      if is_method:
        name = "%s.%s" % (args[0].__class__.__name__, func.__name__)
      else:
        name = "%s.%s" % (func.__module__, func.__name__)

      # Be sure to repr before calling func, because the argument values may change.
      arg_values = {
          name: repr(get_arg_value(name, index, default))
          for name, index, default in args_to_log}

      start = time.time()
      log.add_trace_event("B", start, category, name, arg_values)
      try:
        return func(*args, **kwargs)
      finally:
        end = time.time()
        log.add_trace_event("E", end, category, name, arg_values)
    return traced_function

  no_decorator_arguments = len(args) == 1 and callable(args[0])
  if no_decorator_arguments:
    arg_names = ()
    return get_wrapper(args[0])
  else:
    arg_names = args
    return get_wrapper
