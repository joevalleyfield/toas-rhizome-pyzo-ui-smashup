import faulthandler,os,sys,threading,time
mode=sys.argv[1]
if os.environ.get("RESTART_REPRO_CHILD"):
 print("SUCCESSOR",mode,os.getpid(),flush=True)
 sys.exit(0)
if mode in ("watchdog","cancelled"):
 faulthandler.dump_traceback_later(12)
 if mode=="cancelled": faulthandler.cancel_dump_traceback_later()
if mode=="thread":
 threading.Thread(target=lambda:time.sleep(30),daemon=True).start()
os.environ["RESTART_REPRO_CHILD"]="1"
print("PARENT",mode,os.getpid(),flush=True)
os.execv(sys.executable,[sys.executable,__file__,mode])
