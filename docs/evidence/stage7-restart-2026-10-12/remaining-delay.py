import os,runpy
from spikes.peer_frames.probe_evaluation import EvaluationPoller
original=EvaluationPoller.value
kind=os.environ["DELAY_KIND"]
def delayed(self,shell,expression,phase,**kwargs):
 selected=(kind=="debugger" and (expression=="__import__('os').getpid()" or expression=="local_owner")) or (kind=="execution" and (expression=="'only_a' in globals()" or kwargs.get("label")=="after-pane-move" or phase=="loss")) or (kind=="tools" and expression=="owner_marker")
 if selected:
  expression="(__import__('time').sleep(0.3), ("+expression+"))[1]"
  if os.environ.get("REPRO_OLD_EVALUATION")=="1":
   result=shell._request.eval(expression).result_or_cancel(0.2)
   print("OLD EVALUATION RESULT",phase,expression,repr(result),flush=True)
   return result
 return original(self,shell,expression,phase,**kwargs)
EvaluationPoller.value=delayed
runpy.run_path(os.environ["STAGE7_DELAY_TARGET"],run_name="__main__")
