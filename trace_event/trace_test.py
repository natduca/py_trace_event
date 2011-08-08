# Copyright 2011 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import tempfile
import unittest

from .log import *
from .trace_events import *


class TraceTest(unittest.TestCase):
  def __init__(self, *args):
    """
    Infrastructure for running tests of the tracing system.

    Does not actually run any tests. Look at subclasses for those.
    """
    unittest.TestCase.__init__(self, *args)

  def go(self, cb):
    """
    Enables tracing, runs the provided callback, and if successful, returns a
    TraceEvents object with the results.
    """
    file = tempfile.NamedTemporaryFile()
    trace_enable(open(file.name, 'w+'))

    try:
      cb()
    finally:
      trace_disable()
    e = TraceEvents(trace_filename = file.name)
    file.close()
    return e
