# Copyright 2011 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import json
import tempfile
import time
import unittest
from . import *
from .trace_test import *

class SingleThreadTest(TraceTest):
  def test_one_func(self):
    actual_diff = []
    @trace
    def func1():
      start = time.time()
      time.sleep(0.25)
      end = time.time()
      actual_diff.append(end-start) # Pass via array because of Python scoping

    res = self.go(func1)
    tids = res.findThreadIds()
    self.assertEquals(1, len(tids))
    events = res.findEventsOnThread(tids[0])
    self.assertEquals(2, len(events))
    self.assertEquals('B', events[0]["ph"])
    self.assertEquals('E', events[1]["ph"])
    measured_diff = events[1]["ts"] - events[0]["ts"]
    actual_diff = actual_diff[0]
    self.assertAlmostEqual(actual_diff, measured_diff, 3)

  def test_nested_func(self):
    @trace
    def func1():
      time.sleep(0.25)
      func2()

    @trace
    def func2():
      time.sleep(0.05)

    res = self.go(func1)
    self.assertEquals(1, len(res.findThreadIds()))

    tids = res.findThreadIds()
    self.assertEquals(1, len(tids))
    events = res.findEventsOnThread(tids[0])
    efmt = ["%s %s" % (e["ph"], e["name"]) for e in events]
    self.assertEquals(
      ["B func1",
       "B func2",
       "E func2",
       "E func1"],
      efmt);
