# Copyright 2011 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import atexit
import fcntl
import json
import os
import sys
import threading

__all__ = ["trace_enable", "trace_is_enabled", "trace_disable", "trace_flush"]


_lock = threading.Lock()

_enabled = False
_log_file = None
_log_file_owner = False # tracks whether to write end of file marker on close
_log_file_first_event_pos = -1 # tracks whether to write a ',' at the beginning of flushed events

_cur_events = [] # events that have yet to be buffered

_tls = threading.local() # tls used to detect forking/etc
_atexit_regsitered_for_pid = None

_control_allowed = True

def _locked(fn):
  def locked_fn(*args,**kwargs):
    _lock.acquire()
    try:
      ret = fn(*args,**kwargs)
    finally:
      _lock.release()
    return ret
  return locked_fn

def _disallow_tracing_control():
  global _control_allowed
  _control_allowed = False

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
  if not _control_allowed:
    raise Exception("Tracing control not allowed in child processes.")
  _enabled = True
  global _log_file
  global _log_file_owner
  global _log_file_first_event_pos
  if log_file == None:
    if sys.argv[0] == '':
      n = 'trace_event'
    else:
      n = 'trace_event'
    log_file = open("%s.json" % sys.argv[0], "wb")
  _log_file = log_file
  fcntl.lockf(_log_file.fileno(), fcntl.LOCK_EX)
  _log_file.seek(0, os.SEEK_END)
  _log_file_owner = _log_file.tell() == 0
  if _log_file_owner:
    _log_file.write('{"events": [')
  _log_file.flush()
  _log_file_first_event_pos = _log_file.tell()
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
  if not _control_allowed:
    raise Exception("Tracing control not allowed in child processes.")
  if not _enabled:
    return
  _enabled = False
  _flush(close=True)

def _flush(close=False):
  global _log_file
  fcntl.lockf(_log_file.fileno(), fcntl.LOCK_EX)
  _log_file.seek(0, os.SEEK_END)
  if _log_file.tell() != _log_file_first_event_pos:
    _log_file.write(",")
  _log_file.write(",".join([json.dumps(e) for e in _cur_events]))
  del _cur_events[:]

  if close:
    _log_file.write("]}")
  _log_file.flush()
  fcntl.lockf(_log_file.fileno(), fcntl.LOCK_UN)

  if close:
    _log_file.close()
    _log_file = None

@_locked
def trace_is_enabled():
  """
  Returns whether tracing is enabled.
  """
  return _enabled

@_locked
def add_trace_event(ph, ts, category, name, args=[]):
  global _enabled
  if not _enabled:
    return
  if not hasattr(_tls, 'pid') or _tls.pid != os.getpid():
    _tls.pid = os.getpid()
    global _atexit_regsitered_for_pid
    if _tls.pid != _atexit_regsitered_for_pid:
      _atexit_regsitered_for_pid = _tls.pid
      atexit.register(_trace_disable_atexit)
      _tls.pid = os.getpid()
      del _cur_events[:] # we forked, clear the event buffer!
    tid = threading.current_thread().ident
    if not tid:
      tid = os.getpid()
    _tls.tid = tid

  _cur_events.append({"ph": ph, "category": category,
                      "pid": _tls.pid, "tid": _tls.tid,
                      "ts": ts,
                      "name": name, "args": args});


def _trace_disable_atexit():
  trace_disable()
