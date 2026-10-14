"""Observe probe-owned queries without changing Future behavior."""

import json
from pathlib import Path
import sys
import time


def wrap_query(original, *, probe, method, default_timeout):
    probe = Path(probe).resolve()

    def observe(future, *args, **kwargs):
        caller = sys._getframe(1)
        parent = caller.f_back
        direct = Path(caller.f_code.co_filename).resolve() == probe
        through_poller = (
            Path(caller.f_code.co_filename).name == "acceptanceEvaluation.py"
            and parent is not None
            and Path(parent.f_code.co_filename).resolve() == probe
        )
        selected = direct or through_poller
        source = parent if through_poller else caller
        started = time.monotonic()
        before = future._status

        def record(result, error=None):
            if selected:
                print("QUERY OBSERVATION", json.dumps({
                    "probe": probe.stem,
                    "function": source.f_code.co_name,
                    "method": method,
                    "request": repr(future._req)[:240],
                    "status_before": before,
                    "status_after": future._status,
                    "timeout": kwargs.get("timeout", args[0] if args else default_timeout),
                    "elapsed": round(time.monotonic() - started, 6),
                    "result": repr(result)[:240],
                    "exception": type(error).__name__ if error is not None else None,
                }), flush=True)

        try:
            result = original(future, *args, **kwargs)
        except Exception as error:
            record(None, error)
            raise
        record(result)
        return result

    return observe
