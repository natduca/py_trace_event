# Copyright 2011 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
r"""Instrumentation-based profiling for Python.

trace_event allows you to hand-instrument your code with areas of interest.
When enabled, trace_event logs the start and stop times of these events to a
logfile. These resulting logfiles can be viewed with either Chrome's about:tracing
UI or with the standalone trace_event_viewer available at
  http://www.github.com/natduca/trace_event_viewer/

To use trace event, simply call trace_event_enable and start instrumenting your code:
   from trace_event import *

   if "--trace" in sys.argv:
     trace_enable("myfile.trace")

   @traced
   def foo():
     ...

   class MyFoo(object):
     @tracedmethod
     def bar(self):
       ...

trace_event records trace events to an in-memory buffer. If your application is
long running and you want to see the results of a trace before it exits, you can call
trace_flush to write any in-memory events to disk.

To help intregrating trace_event into existing codebases that dont want to add
trace_event as a dependancy, trace_event is split into an import shim
(trace_event.py) and an implementaiton (trace_event_impl/*). You can copy the
shim, trace_event.py, directly into your including codebase. If the
trace_event_impl is not found, the shim will simply noop.

trace_event is safe with regard to Python threads. Simply trace as you normally would and each
thread's timing will show up in the trace file.

Multiple processes can safely output into a single trace_event logfile. If you
fork after enabling tracing, the child process will continue outputting to the
logfile. Use of the multiprocessing module will work as well. In both cases,
however, note that disabling tracing in the parent process will not stop tracing
in the child processes.
"""

try:
  import trace_event_impl
except ImportError:
  trace_event_impl = None

def trace_can_enable():
  """
  Returns True if a trace_event_impl was found. If false,
  trace_enable will fail. Regular tracing methods, including
  trace_begin and trace_end, will simply be no-ops.
  """
  return trace_event_impl != None

if trace_event_impl:
  import time

  def trace_is_enabled():
    return trace_event_impl.trace_is_enabled()

  def trace_enable(logfile):
    return trace_event_impl.trace_enable(logfile)

  def trace_disable():
    return trace_event_impl.trace_disable()

  def trace_flush():
    trace_event_impl.trace_flush()

  def trace_begin(name):
    trace_event_impl.add_trace_event("B", time.time(), "python", name)

  def trace_end(name):
    trace_event_impl.add_trace_event("E", time.time(), "python", name)

  def traced(fn):
    return trace_event_impl.traced(fn)

  def tracedmethod(fn):
    return trace_event_impl.tracedmethod(fn)

else:
  def trace_enable():
    raise TraceException("Cannot enable trace_event. No trace_event_impl module found.")

  def trace_disable():
    raise TraceException("Cannot disable trace_event. No trace_event_impl module found.")

  def trace_is_enabled():
    return False

  def trace_flush():
    return

  def trace_begin(self, name):
    return

  def trace_end(self, name):
    return

  def traced(fn):
    return fn

  def tracedmethod(fn):
    return fn


trace_enable.__doc__ = """Enables tracing.

  Once enabled, the enabled bit propagates to forked processes and
  multiprocessing subprocesses. Regular child processes, e.g. those created via
  os.system/popen, or subprocess.Popen instances, will not get traced. You can,
  however, enable tracing on those subprocess manually.

  Trace files are multiprocess safe, so you can have multiple processes
  outputting to the same tracelog at once.

  log_file can be one of three things:

    None: a logfile is opened based on sys[argv], namely
          "./" + sys.argv[0] + ".json"

    string: a logfile of the given name is opened.

    file-like object: the fileno() is is used. The underlying file descriptor
                      must support fcntl.lockf() operations.
  """

trace_disable.__doc__ =   """Disables tracing, if enabled.

  Will not disable tracing on any existing child proceses that were forked
  from this process. You must disable them yourself.
  """

trace_flush.__doc__ = """Flushes any currently-recorded trace data to disk.

  trace_event records traces into an in-memory buffer for efficiency. Flushing
  is only done at process exit or when this method is called.
  """

trace_flush.__doc__ = """Returns whether tracing is enabled.
  """

trace_begin.__doc__ = """Records the beginning of an event of the given name.

  The building block for performance tracing. A typical example is:
     from trace_event import *
     def something_heavy():
        trace_begin("something_heavy")

        trace_begin("read")
        try:
          lines = open().readlines()
        finally:
          trace_end("read)

        trace_begin("parse")
        try:
          parse(lines)
        finally:
          trace_end("parse")

        trace_end("something_heavy")

  Note that a trace_end method must be issued for every trace_begin method. When
  tracing around methods that might throw exceptions, you should use a try-finally
  pattern to ensure that the trace_end method is called.

  See the documentation for the @traced and @tracedmethod decorator for a simpler way to instrument
  functions and methods.
  """

trace_end.__doc__ = """Records the end of an event of the given name.

  See the documentation for trace_begin for more information.

  Make sure to issue a trace_end for every trace_begin issued. Failure to pair
  these calls will lead to bizarrely tall looking traces in the
  trace_event_viewer UI.
  """

traced.__doc__ = """
  Traces the provided function, using the function name for the actual generated event.

  You can use this on class methods, but using @tracedmethod will give you not only the function
  name but also its controlling class. E.g.;
    class Foo:

      @traced
      def bar():
        # generates traces for "bar"
        pass

      @tracedmethod
      def bar():
        # generates traces for "Foo.bar"
        pass

  Prefer this method over the explicit trace_begin and trace_end methods whenever you are tracing
  the start and stop of a function. It automatically issues trace_begin/end events, even when the wrapped
  function throws.
  """

tracedmethod.__doc__ = """
  Traces the provided classmethod, using the class name and function name for the actual generated event.

  This will only work on class methods, as it relies on the presence of the self argument to determine
  the owning class for the method. To trace a function, use the @traced decorator.

    class Foo:
      @traced
      def bar():
        # generates traces for "bar"
        pass

      @tracedmethod
      def bar():
        # generates traces for "Foo.bar"
        pass

    @tracedmethod # <--- THIS WILL FAIL!!! Use @traced instead.
    def func():
       pass

  Prefer this method over the explicit trace_begin and trace_end methods whenever you are tracing
  the start and stop of a function. It automatically issues trace_begin/end events, even when the wrapped
  function throws.
  """
