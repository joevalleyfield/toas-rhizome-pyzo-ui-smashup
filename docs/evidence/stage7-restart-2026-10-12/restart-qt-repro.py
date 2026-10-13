import os,sys
mode=sys.argv[1]
if os.environ.get("RESTART_REPRO_CHILD"):
 print("SUCCESSOR",mode,os.getpid(),flush=True)
 sys.exit(0)
from PySide6 import QtCore,QtWidgets
app=None
if mode!="import":app=QtWidgets.QApplication([])
widget=None
if mode in ("widget","callback","destroy"):
 widget=QtWidgets.QWidget()
 widget.show()
def replace():
 os.environ["RESTART_REPRO_CHILD"]="1"
 print("PARENT",mode,os.getpid(),flush=True)
 os.execv(sys.executable,[sys.executable,__file__,mode])
if mode=="callback":
 QtCore.QTimer.singleShot(200,replace)
 app.exec()
else:
 if mode=="destroy":
  import shiboken6
  shiboken6.delete(widget)
  shiboken6.delete(app)
 replace()
