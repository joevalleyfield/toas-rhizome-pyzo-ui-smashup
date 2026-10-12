# Windows workspace tools and contextual checkpoints

Windows 11 x64, Python 3.12.13 / PySide6 6.11.1 prepared runtime.

- tools.log/xml: immutable generation regression, scheduling and live tools/restore; 11 passed, 31.84s.
- units.log/xml: full units; 710 passed, 41 skipped, 39.16s.
- retention.log/xml: broader real-process recovery/publication/retention controls; 9 passed, 67.19s.

Preference-only edits now participate in automatic save generations. The writer
uses immutable captured owner profiles. Automatic publication took 1.078s within
the unchanged four-second check. All tool and restore assertions remain.

The prior full-suite restart parent status failures remain pending.
