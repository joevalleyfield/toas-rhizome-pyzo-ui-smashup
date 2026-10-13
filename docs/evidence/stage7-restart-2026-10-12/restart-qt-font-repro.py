import os,sys
from pathlib import Path
mode=sys.argv[1]
if os.environ.get("RESTART_REPRO_CHILD"):
 print("SUCCESSOR",mode,os.getpid(),flush=True)
 sys.exit(0)
from PySide6 import QtCore,QtGui,QtWidgets,QtPrintSupport
app=None
if mode!="import":app=QtWidgets.QApplication([])
widget=None
if mode in ("text","callback","destroy","font","removed"):
 widget=QtWidgets.QPlainTextEdit("font cache restart")
 font=QtGui.QFontDatabase.addApplicationFont(str(Path(__file__).parent/"restart-pristine-base/pyzo/resources/fonts/DejaVuSansMono.ttf"))
 print("FONT",font,QtGui.QFontDatabase.applicationFontFamilies(font),flush=True)
 widget.setFont(QtGui.QFont("DejaVu Sans Mono"))
 widget.show()
if mode=="fonts":print(len(QtGui.QFontDatabase.families()),flush=True)
def replace():
 os.environ["RESTART_REPRO_CHILD"]="1"
 print("PARENT",mode,os.getpid(),flush=True)
 os.execv(sys.executable,[sys.executable,__file__,mode])
if mode=="callback":
 QtCore.QTimer.singleShot(200,replace)
 app.exec()
else:
 if mode=="removed":QtGui.QFontDatabase.removeAllApplicationFonts()
 if mode=="destroy":
  import shiboken6
  shiboken6.delete(widget)
  shiboken6.delete(app)
 replace()
