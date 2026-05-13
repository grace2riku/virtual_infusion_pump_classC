"""Detection group package (ARCH-006) — Inc.2 alarm-detector units.

This package collects the detection units introduced in Inc.2 per SAD-VIP-001
v0.2 §4.3.2:

* UNIT-006.1 Occlusion Detector (`occlusion.py`, Step 20 X — TDD seed)
* UNIT-006.2 Air-Bubble Detector (planned)
* UNIT-006.3 Reservoir Empty Detector (planned)
* UNIT-006.4 Alarm Task Watchdog (planned)
* UNIT-006.5 Alarm Path Redundancy (planned)
* UNIT-006.6 Battery Low Detector (planned)

Shared protocols (sensor I/F, alarm reporter, state-transition requester) live
in :mod:`vip_detection.protocols` so successor units can reuse them without
introducing cyclic imports.
"""
