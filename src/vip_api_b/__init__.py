"""API subsystem, class B (UNIT-005.3 per SDD-VIP-001 §4, SEP-001 separation).

Validation API separated to class B per SAD §9 (logical separation by
abstract interface, one-way dependency, frozen data, static-analysis rules).
Dependencies must flow B -> C only; C -> B is forbidden and verified by mypy
import graph analysis.
"""
