# Copyright 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import multiprocessing
import tempfile
import time
import unittest
from . import *
from .trace_test import *

import os

def PoolWorker():
  @trace
  def do_work():
    time.sleep(0.25)
  do_work()
  trace_flush() # todo, reduce need for this...

class MultiprocessingTest(TraceTest):
  def test_one_func(self):
    @trace
    def work():
      p = multiprocessing.Pool(1)
      p.apply(PoolWorker, ())
      p.close()
      p.terminate()
      p.join()
    res = self.go(work)
    work_events = res.findByName('work')
    do_work_events = res.findByName('do_work')
    self.assertEquals(2, len(work_events))
    self.assertEquals(2, len(do_work_events))

