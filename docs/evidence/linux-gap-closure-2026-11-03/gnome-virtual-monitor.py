import sys, json, time
import gi
gi.require_version('Gst','1.0')
from gi.repository import Gio, GLib, Gst
Gst.init(None)
bus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
def call(dest,path,iface,method,sig=None,args=()):
 return bus.call_sync(dest,path,iface,method,GLib.Variant(sig,args) if sig else None,None,Gio.DBusCallFlags.NONE,15000,None).unpack()
def intro(dest,path):
 return call(dest,path,'org.freedesktop.DBus.Introspectable','Introspect')[0]
sc='org.gnome.Mutter.ScreenCast'; si=sc+'.Session'
sp=call(sc,'/org/gnome/Mutter/ScreenCast',sc,'CreateSession','(a{sv})',({},))[0]
print('SCREENCAST SESSION CREATED',flush=True)
stream=call(sc,sp,si,'RecordVirtual','(a{sv})',({'is-platform':GLib.Variant('b',True)},))[0]
print('MONITOR STREAM CREATED',flush=True)
node=[]
bus.signal_subscribe(sc,sc+'.Stream','PipeWireStreamAdded',stream,None,Gio.DBusSignalFlags.NONE,lambda *args:node.append(args[-1].unpack()[0]))
call(sc,sp,si,'Start')
end=time.monotonic()+10
while not node and time.monotonic()<end:
 GLib.MainContext.default().iteration(False); time.sleep(.01)
print('NODE',node,flush=True)
if not node: raise RuntimeError('no PipeWire stream')
pipeline=Gst.parse_launch(f'pipewiresrc path={node[0]} do-timestamp=true ! video/x-raw,width=1920,height=1080,framerate=0/1,max-framerate=60/1 ! queue leaky=downstream max-size-buffers=1 max-size-time=0 max-size-bytes=0 ! videoconvert ! pngenc ! appsink name=sink sync=false max-buffers=1 drop=true')
sink=pipeline.get_by_name('sink'); pipeline.set_state(Gst.State.PLAYING)
def wait(seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  while GLib.MainContext.default().pending(): GLib.MainContext.default().iteration(False)
  time.sleep(.01)
def action(a):
 kind=a[0]
 if kind=='wait':wait(a[1])
 elif kind=='shot':
  sample=sink.emit('try-pull-sample',0)
  for _ in range(8):
   wait(.1)
   newer=sink.emit('try-pull-sample',100*Gst.MSECOND)
   if newer: sample=newer
  if not sample: sample=sink.emit('try-pull-sample',5*Gst.SECOND)
  if not sample:raise RuntimeError('no screenshot sample')
  buf=sample.get_buffer(); data=buf.extract_dup(0,buf.get_size())
  open(a[1],'wb').write(data);print('SCREENSHOT',a[1],len(data),flush=True)
 else:raise ValueError(kind)
print('READY',flush=True)
try:
 for line in sys.stdin:
  try:
   request=json.loads(line)
   if request=='quit':break
   for a in request:action(a)
   print('DONE',flush=True)
  except Exception as e: print('ERROR',repr(e),flush=True)
finally:
 pipeline.set_state(Gst.State.NULL)
 call(sc,sp,si,'Stop')
