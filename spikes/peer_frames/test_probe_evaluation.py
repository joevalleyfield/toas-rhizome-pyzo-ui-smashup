from types import SimpleNamespace as NS
import pytest
from spikes.peer_frames.probe_evaluation import EvaluationPending, EvaluationPoller

class Future:
    def __init__(self, value):
        self.value = value
        self.delayed = True
    def result(self, timeout):
        assert timeout == 0.2
        if self.delayed:
            self.delayed = False
            raise TimeoutError
        return self.value

def test_delayed_false_is_not_timeout_or_incorrect_execution():
    calls = []
    future = Future(False)
    shell = NS(_context=object())
    shell._request = NS(eval=lambda expression: calls.append(expression) or future)
    # SimpleNamespace is unhashable; the actual shell is a Qt object.
    class Shell: pass
    target = Shell();target.__dict__.update(shell.__dict__)
    poller = EvaluationPoller()
    with pytest.raises(EvaluationPending):poller.value(target, "never_run", "cell")
    assert poller.value(target, "never_run", "cell") is False
    assert calls == ["never_run"]
    assert poller.value(target, "never_run", "cell") is False
    assert calls == ["never_run"]

def test_delayed_distinct_pids_and_actual_bad_value_preserve_assertion():
    class Shell:
        def __init__(self, pid):
            self._context = object()
            self.future = Future(pid)
            self._request = NS(eval=lambda _: self.future)
    a,b=Shell(101),Shell(202);poller=EvaluationPoller()
    for shell in (a,b):
        with pytest.raises(EvaluationPending):poller.value(shell, "pid", "ready")
    pids=[poller.value(shell,"pid","ready") for shell in (a,b)]
    assert len(set(pids)) == 2 and all(isinstance(pid,int) for pid in pids)
    b.future.value = "not-a-pid"
    values=[poller.value(shell,"pid","new-phase") for shell in (a,b)]
    with pytest.raises(AssertionError):
        assert len(set(values)) == 2 and all(isinstance(pid,int) for pid in values)


def test_name_not_yet_defined_is_retried_without_resetting_pending_request():
    class Shell: pass
    shell = Shell();shell._context=object()
    futures=[Future("Error evaluating: cell_value"),Future(101)]
    for future in futures:future.delayed=False
    shell._request=NS(eval=lambda _: futures.pop(0))
    poller=EvaluationPoller()
    assert poller.value(shell,"cell_value","cell") == "Error evaluating: cell_value"
    assert poller.value(shell,"cell_value","cell") == 101


def test_after_move_label_queries_fresh_instead_of_using_prior_response():
    class Shell: pass
    shell=Shell();shell._context=object()
    a,b=Future(11),Future(99);a.delayed=b.delayed=False
    calls=[];futures=[a,b]
    shell._request=NS(eval=lambda expr:calls.append(expr) or futures.pop(0))
    poller=EvaluationPoller()
    assert poller.value(shell,"assigned_value","values") == 11
    assert poller.value(shell,"assigned_value","values",label="after-pane-move") == 99
    assert calls == ["assigned_value","assigned_value"]
