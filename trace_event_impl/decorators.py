# Copyright 2011 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import inspect
import log
import os
import time
import threading
import functools

def traced(func):
  if inspect.isgeneratorfunction(func):
    raise Exception("Can not trace generators.")

  category = "python"

  @functools.wraps(func)
  def traced_function(*args,**kwargs):
    if not log._enabled:
      return func(*args,**kwargs)
    start = time.time()
    log.add_trace_event("B", start, category, func.__name__)
    try:
      return func(*args,**kwargs)
    finally:
      end = time.time()
      log.add_trace_event("E", end, category, func.__name__)
  return traced_function

def tracedmethod(classmethod):
  if inspect.isgeneratorfunction(classmethod):
    raise Exception("Can not trace generators.")
    trace_generator(f, category)

  category = "python"
  fname = [None]

  @functools.wraps(classmethod)
  def traced_method(*args,**kwargs):
    if not log._enabled:
      return classmethod(*args,**kwargs)
    if not fname[0]:
      fname[0] = "%s.%s" % (args[0].__class__.__name__, classmethod.__name__)
    start = time.time()
    log.add_trace_event("B", start, category, fname[0])
    try:
      return classmethod(*args,**kwargs)
    finally:
      end = time.time()
      log.add_trace_event("E", end, category, fname[0])
  return traced_method

