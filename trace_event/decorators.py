# Copyright 2011 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import log
import os
import time
import threading

__all__ = ["trace"]

def trace(f,category=""):
  def traced_function(*args,**kwargs):
    if not log._enabled:
      return f(*args,**kwargs)
    start = time.time()
    log.add_trace_event("B", start, category, f.__name__)
    r = f(*args,**kwargs)
    end = time.time()
    log.add_trace_event("E", end, category, f.__name__)
    return r
  traced_function.__name__ = f.__name__
  traced_function.__doc__ = f.__doc__
  traced_function.__dict__.update(f.__dict__)
  return traced_function
