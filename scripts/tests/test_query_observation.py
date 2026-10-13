"""Observation preserves query values, pending errors, and caller ownership."""

from types import SimpleNamespace as NS

import pytest

from scripts.query_observation import wrap_query


@pytest.mark.parametrize("method", ["result", "result_or_cancel"])
@pytest.mark.parametrize("value", [False, None, 42])
def test_values_and_arguments_are_preserved(method, value, capsys):
    calls = []
    future = NS(_status=0, _req=b"probe expression")
    def original(target, *args, **kwargs):
        calls.append((target, args, kwargs))
        target._status = 4
        return value
    wrapped = wrap_query(original, probe=__file__, method=method, default_timeout=None)
    assert wrapped(future, timeout=0.2) is value
    assert calls == [(future, (), {"timeout": 0.2})]
    output = capsys.readouterr().out
    assert "QUERY OBSERVATION" in output
    assert '"exception": null' in output


@pytest.mark.parametrize("error", [TimeoutError("pending"), ValueError("query failed")])
def test_query_exceptions_are_preserved(error, capsys):
    future = NS(_status=0, _req=b"probe expression")
    def original(target, timeout):
        raise error
    wrapped = wrap_query(original, probe=__file__, method="result", default_timeout=None)
    with pytest.raises(type(error)) as caught:
        wrapped(future, 0.2)
    assert caught.value is error
    assert type(error).__name__ in capsys.readouterr().out


def test_pending_poller_call_is_observed_from_owning_probe(capsys):
    future = NS(_status=4, _req=b"probe expression")
    wrapped = wrap_query(lambda target, timeout: False, probe=__file__, method="result", default_timeout=None)
    namespace = {"wrapped": wrapped, "future": future}
    exec(compile("def evaluate(): return wrapped(future, 0.2)", "acceptanceEvaluation.py", "exec"), namespace)
    assert namespace["evaluate"]() is False
    assert "QUERY OBSERVATION" in capsys.readouterr().out


def test_unrelated_query_is_not_logged(tmp_path, capsys):
    future = NS(_status=4, _req=b"unrelated expression")
    wrapped = wrap_query(lambda target: None, probe=tmp_path / "other_probe.py", method="result", default_timeout=None)
    assert wrapped(future) is None
    assert capsys.readouterr().out == ""
