#!/usr/bin/env python3
"""
AI-OS CC2 — Live Demo Script
Boots the system, runs a fixed demo sequence, and prints the results.
This is the single repeatable flow for live-testing AIOS-CC2.

Usage:
    python demo.py              # run demo (with a 0.3 s pause between steps)
    python demo.py --fast       # no pauses (CI / quick check)
    python demo.py --trace      # also write demo trace to demo_trace.log
"""
import argparse
import os
import sys
import time

_here = os.path.dirname(os.path.abspath(__file__))
for _p in (_here, os.path.join(_here, "aios")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

DEMO_STEPS = [
    # (command, human label)
    ("1.1",   "Full System Report"),
    ("1.2",   "Layer Health (Layers 1-7)"),
    ("1.3",   "Subsystem List"),
    ("4.1",   "Virtual CPU Status"),
    ("4.4",   "Live Sensor Readings"),
    ("5.1",   "Network Interfaces"),
    ("5.3",   "Heartbeat Status"),
    ("6.1",   "Identity / Security Status"),
    ("7.1",   "Cloud Status"),
    ("10.1",  "AuraEngine Full Status"),
    ("11.1",  "Full Diagnostic Report"),
    ("11.2",  "Health Check All"),
    ("13.1",  "Legal Compliance Status"),
    ("15.5",  "Full Audit Dump"),
]

BANNER = r"""
  ╔══════════════════════════════════════════════════════╗
  ║        AI-OS CC2 — LIVE DEMO SEQUENCE                ║
  ║        Operator: Chris  |  Version: 2.0.0-CC2        ║
  ╚══════════════════════════════════════════════════════╝
"""


def _parse_args():
    p = argparse.ArgumentParser(description="AI-OS CC2 live demo")
    p.add_argument("--fast", action="store_true", help="No pauses between steps")
    p.add_argument("--trace", action="store_true", help="Write demo trace to demo_trace.log")
    return p.parse_args()


def run_demo(fast: bool = False, trace: bool = False) -> int:
    print(BANNER)
    step_delay = 0.0 if fast else 0.3

    # Boot
    print("  Booting AI-OS subsystems...\n")
    try:
        from aios.main import boot_subsystems
        t0 = time.time()
        subsystems = boot_subsystems()
        boot_ms = int((time.time() - t0) * 1000)
        cc = subsystems["cc"]
    except Exception as exc:
        print(f"\n  ✗ BOOT FAILED: {exc}")
        return 1

    if trace:
        trace_path = os.path.join(_here, "demo_trace.log")
        cc.set_trace_file(trace_path)
        print(f"\n  [TRACE] Writing trace to: {trace_path}")

    # Force one heartbeat sync so it shows as healthy
    hb = subsystems.get("heartbeat")
    if hb:
        hb.beat_sync()

    print(f"\n  ✓ Boot complete in {boot_ms} ms")
    print(f"  ✓ Operator  : {cc._get_operator()}")
    print(f"  ✓ Subsystems: {len([v for v in subsystems.values() if v is not None])}")
    print()

    # Run demo steps
    passed = 0
    failed = 0
    for i, (cmd, label) in enumerate(DEMO_STEPS, start=1):
        prefix = f"  [{i:02d}/{len(DEMO_STEPS):02d}]  CMD {cmd:<6}  {label}"
        try:
            result = cc.handle_command(cmd)
            lines = [ln for ln in result.splitlines() if ln.strip()]
            summary = lines[1] if len(lines) > 1 else (lines[0] if lines else "")
            summary = summary.strip()[:60]
            print(f"{prefix}")
            print(f"           → {summary}")
            passed += 1
        except Exception as exc:
            print(f"{prefix}")
            print(f"           ✗ ERROR: {exc}")
            failed += 1

        if step_delay:
            time.sleep(step_delay)

    # Cloud demo
    print()
    print(f"  [CLOUD] Starting cloud layer...")
    try:
        cloud_start = cc.handle_command("7.3")
        print(f"  → {cloud_start.strip()[:80]}")
        time.sleep(0.1)
        cloud_status = cc.handle_command("7.1")
        for line in cloud_status.splitlines():
            if line.strip():
                print(f"  → {line.strip()}")
    except Exception as exc:
        print(f"  ✗ Cloud demo error: {exc}")
        failed += 1

    # Summary
    total = passed + failed
    status = "PASS" if failed == 0 else "FAIL"
    print()
    print("  " + "═" * 54)
    print(f"  DEMO COMPLETE: {status}  ({passed}/{total} steps passed)")
    print("  " + "═" * 54)
    if failed == 0:
        print("  ✓ System is live-demo ready.\n")
    else:
        print(f"  ✗ {failed} step(s) failed — see output above.\n")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    args = _parse_args()
    sys.exit(run_demo(fast=args.fast, trace=args.trace))
