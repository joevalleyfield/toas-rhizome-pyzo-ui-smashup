import gi,json
gi.require_version('Gio','2.0')
from gi.repository import Gio,GLib
bus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
def call(method,signature=None,args=()):
 return bus.call_sync('org.gnome.Mutter.DisplayConfig','/org/gnome/Mutter/DisplayConfig','org.gnome.Mutter.DisplayConfig',method,GLib.Variant(signature,args) if signature else None,None,Gio.DBusCallFlags.NONE,10000,None).unpack()
s=call('GetCurrentState');print(s,flush=True)
assert len(s[1])==2
logical=[]
for old in s[2]:
 x,y,scale,transform,primary,monitors,properties=old
 modes=[]
 for spec in monitors:
  monitor=next(m for m in s[1] if m[0]==spec)
  mode=next((m for m in monitor[1] if m[6].get('is-current')),monitor[1][0])
  if spec[0].startswith('Meta-'):
   assert 2.0 in mode[5],mode
   scale=2.0
  modes.append((spec[0],mode[0],{}))
 logical.append((x,y,scale,transform,primary,modes))
call('ApplyMonitorsConfig','(uua(iiduba(ssa{sv}))a{sv})',(s[0],1,logical,{}))
print('MIXED SCALE APPLIED',flush=True)
