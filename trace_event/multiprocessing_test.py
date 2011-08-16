# Copyright 2011 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import multiprocessing
import tempfile
import time
import unittest
from . import *
from .trace_test import *

import os

def DoWork():
  """
  Sadly, you can't @trace toplevel functions, as it prevents them
  from being called in the child process. :(

  So, we wrap the function of interest.
  """
  @trace
  def do_work():
    time.sleep(0.25)
  do_work()

def AssertTracingEnabled():
  assert trace_is_enabled()

def AssertTracingDisabled():
  assert not trace_is_enabled()

def TryToDisableTracing():
  trace_disable();

class MultiprocessingTest(TraceTest):
  def test_shimmed(self):
    p = multiprocessing.Process()
    self.assertTrue(hasattr(p, "_shimmed_by_trace_event"))

  def test_trace_enable_throws_in_child(self):
    @trace
    def work():
      p = multiprocessing.Pool(1)
      self.assertRaises(Exception, lambda: p.apply(TryToDisableTracing, ()))
      p.close()
      p.terminate()
      p.join()
    res = self.go(work)

  def test_trace_enabled_in_child(self):
    @trace
    def work():
      p = multiprocessing.Pool(1)
      p.apply(AssertTracingEnabled, ())
      p.close()
      p.terminate()
      p.join()
    res = self.go(work)

  def test_one_func(self):
    @trace
    def work():
      p = multiprocessing.Pool(1)
      p.apply(DoWork, ())
      p.close()
      p.terminate()
      p.join()
    res = self.go(work)
    work_events = res.findByName('work')
    do_work_events = res.findByName('do_work')
    self.assertEquals(2, len(work_events))
    self.assertEquals(2, len(do_work_events))

