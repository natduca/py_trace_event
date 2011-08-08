# Copyright 2011 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import atexit
import fcntl
import json
import os
import sys
import threading

__all__ = ["trace_enable", "trace_disable", "trace_flush"]


_lock = threading.Lock()

_enabled = False
_log_file = None
_log_file_owner = False

_cur_events = []

_tls = threading.local()
_pid = os.getpid()

def _locked(fn):
  def locked_fn(*args,**kwargs):
    _lock.acquire()
    try:
      ret = fn(*args,**kwargs)
    finally:
      _lock.release()
    return ret
  return locked_fn

@_locked
def trace_enable(log_file=None):
  """
  Enables tracing.

  New multiprocessing.Process will inherit the enabled state.

  log_file: if not provided, uses sys.argv[0] or trace_event.json
  """
  global _enabled
  if _enabled:
    raise Exception("Already enabled")
  _enabled = True
  global _log_file
  global _log_file_owner
  if log_file == None:
    if sys.argv[0] == '':
      n = 'trace_event'
    else:
      n = 'trace_event'
    log_file = open("%s.json" % sys.argv[0], "w")
  _log_file = log_file
  fcntl.lockf(_log_file.fileno(), fcntl.LOCK_EX)
  _log_file.seek(0, 2)
  _log_file_owner = _log_file.tell() == 0
  _log_file.write('{"events": [')
  fcntl.lockf(_log_file.fileno(), fcntl.LOCK_UN)

@_locked
def trace_flush():
  """
  Flushes any currently-recorded trace data to disk.
  """
  _flush()

@_locked
def trace_disable():
  """
  Disables tracing, if enabled. Will not disable tracing
  on any existing child proceses.
  """
  global _enabled
  if not _enabled:
    return
  _enabled = False
  _flush(close=True)

def _flush(close=False):
  global _log_file
  fcntl.lockf(_log_file.fileno(), fcntl.LOCK_EX)
  _log_file.seek(0, 2)
  _log_file.write(",".join([json.dumps(e) for e in _cur_events]))
  del _cur_events[:]

  if close:
    _log_file.write("]}")
  fcntl.lockf(_log_file.fileno(), fcntl.LOCK_UN)

  if close:
    _log_file.close()
    _log_file = None

@_locked
def add_trace_event(ph, ts, category, name, args=[]):
  global _enabled
  if not _enabled:
    return
  tid = threading.current_thread().ident
  _cur_events.append({"ph": ph, "category": category,
                      "pid": _pid, "tid": tid,
                      "ts": ts,
                      "name": name, "args": args});


atexit.register(trace_disable)

