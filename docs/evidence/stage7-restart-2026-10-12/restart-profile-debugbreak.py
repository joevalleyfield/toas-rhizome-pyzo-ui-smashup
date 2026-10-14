import os,runpy,faulthandler,threading,time
original_exec=os.execv
mode=os.environ["RESTART_DIAGNOSTIC"]
def replace(path,args):
 print("DIAGNOSTIC BEFORE EXEC",mode,[(t.name,t.is_alive(),t.daemon) for t in threading.enumerate()],flush=True)
 if mode=="cancel-watchdog": faulthandler.cancel_dump_traceback_later()
 if mode=="wait-threads":
  for t in threading.enumerate():
   if t is not threading.current_thread() and t.daemon:t.join(0.5)
  print("DIAGNOSTIC AFTER JOIN",[(t.name,t.is_alive()) for t in threading.enumerate()],flush=True)
 if mode=="delete-app":
  from pyzo.qt import QtWidgets
  import shiboken6
  shiboken6.delete(QtWidgets.QApplication.instance())
 import ctypes
 ctypes.windll.kernel32.DebugBreak()
 original_exec(path,args)
os.execv=replace
runpy.run_path(os.environ["RESTART_DIAGNOSTIC_TARGET"],run_name="__main__")
