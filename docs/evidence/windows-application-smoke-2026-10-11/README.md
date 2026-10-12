# Windows application smoke

Windows 11 x64, prepared Python 3.12.13 / PySide6 6.11.1 runtime.

- units.log/xml: 709 passed, 41 skipped, 38.90s.
- smoke.log/xml: peer + legacy success and intentional failures, 2 passed, 43.85s.
- final.log/xml: final debugger units, owner audit, smoke and real-kernel debugger replay.

The ten-second peer smoke deadline and all line, owner and kernel-affinity
assertions remain. Optional symlink skips follow the user-approved platform policy.
Full live suite was not rerun in this step; prior tools/restart failures remain.

Final focused replay: 18 passed, 1 optional symlink skip, 62.86s.
