#!/usr/bin/env python3
"""
AI-OS CC2 — Health Check Script
Usage:
    python health_check.py              # boot + check, exit 0 if healthy
    python health_check.py --verbose    # detailed report
    python health_check.py --json       # JSON output (for CI / automation)

Exit codes:
    0 — all checks passed
    1 — one or more checks failed
    2 — fatal boot error
"""
import argparse
import json
import os
import sys
import time

_here = os.path.dirname(os.path.abspath(__file__))
for _p in (_here, os.path.join(_here, "aios")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _parse_args():
    p = argparse.ArgumentParser(description="AI-OS CC2 health check")
    p.add_argument("--verbose", "-v", action="store_true", help="Detailed output")
    p.add_argument("--json", action="store_true", help="JSON output")
    return p.parse_args()


def run_health_check(verbose: bool = False, json_output: bool = False):
    results = {}
    passed = 0
    failed = 0
    errors = []

    # ── Boot subsystems ────────────────────────────────────────────────────
    try:
        from aios.main import boot_subsystems
        subsystems = boot_subsystems()
        cc = subsystems["cc"]
    except Exception as exc:
        msg = f"FATAL: boot_subsystems() failed: {exc}"
        if json_output:
            print(json.dumps({"status": "FATAL", "error": str(exc)}, indent=2))
        else:
            print(msg)
        return 2

    # Give the endless loop and heartbeat a moment to start
    time.sleep(0.5)

    # ── Individual component checks ────────────────────────────────────────
    status = cc.get_status_dict()

    CHECK_COMPONENTS = [
        "state", "policy", "security", "identity", "memory",
        "vcpu", "vmem", "vstorage", "vnet", "vsensors",
        "bridge", "mesh", "aura", "cloud",
    ]

    for name in CHECK_COMPONENTS:
        comp = status.get(name, {})
        if isinstance(comp, dict):
            healthy = comp.get("healthy", False)
        else:
            healthy = False
            comp = {}
        results[name] = {"healthy": healthy, "detail": comp}
        if healthy:
            passed += 1
        else:
            failed += 1
            errors.append(f"{name}: not healthy — {comp}")

    # ── Heartbeat check (separate — may start slightly late) ───────────────
    hb = subsystems.get("heartbeat")
    hb_ok = False
    if hb:
        # Force one synchronous beat
        hb.beat_sync()
        hb_status = hb.status()
        hb_ok = hb_status.get("beat_count", 0) > 0
    results["heartbeat"] = {"healthy": hb_ok}
    if hb_ok:
        passed += 1
    else:
        failed += 1
        errors.append("heartbeat: no beats recorded")

    # ── Command routing checks ─────────────────────────────────────────────
    SMOKE_COMMANDS = [
        ("1.1",  "Full System Report",     "version"),
        ("1.2",  "Layer Health",           "Layer"),
        ("1.3",  "Subsystem List",         "Subsystem"),
        ("4.1",  "Virtual CPU Status",     "VirtualCPU"),
        ("5.3",  "Heartbeat Status",       "HeartbeatSystem"),
        ("11.1", "Full Diagnostic Report", "Diagnostic"),
        ("11.2", "Health Check All",       "✓"),
    ]
    cmd_pass = 0
    cmd_fail = 0
    cmd_errors = []
    for cmd, label, expected_substr in SMOKE_COMMANDS:
        try:
            result = cc.handle_command(cmd)
            if expected_substr in result:
                cmd_pass += 1
            else:
                cmd_fail += 1
                cmd_errors.append(f"  {cmd} ({label}): expected '{expected_substr}' in output")
        except Exception as exc:
            cmd_fail += 1
            cmd_errors.append(f"  {cmd} ({label}): EXCEPTION {exc}")

    results["command_routing"] = {
        "healthy": cmd_fail == 0,
        "passed": cmd_pass,
        "failed": cmd_fail,
        "errors": cmd_errors,
    }
    if cmd_fail == 0:
        passed += 1
    else:
        failed += 1
        errors.extend(cmd_errors)

    # ── Web API health check (in-process) ──────────────────────────────────
    try:
        api_status = cc.get_status_dict()
        api_ok = api_status.get("running", False)
    except Exception as exc:
        api_ok = False
        errors.append(f"api_status: {exc}")
    results["api_status_dict"] = {"healthy": api_ok}
    if api_ok:
        passed += 1
    else:
        failed += 1
        errors.append("api_status_dict: running=False")

    # ── Summary ────────────────────────────────────────────────────────────
    total = passed + failed
    overall = "PASS" if failed == 0 else "FAIL"

    if json_output:
        out = {
            "status": overall,
            "passed": passed,
            "failed": failed,
            "total": total,
            "components": results,
            "errors": errors,
        }
        print(json.dumps(out, indent=2, default=str))
    else:
        width = 56
        print()
        print("=" * width)
        print(f"  AI-OS CC2 — Health Check Results")
        print("=" * width)
        for name, r in results.items():
            if name == "command_routing":
                sym = "✓" if r["healthy"] else "✗"
                print(f"  {sym}  command_routing  ({r['passed']}/{r['passed']+r['failed']} commands OK)")
            else:
                sym = "✓" if r["healthy"] else "✗"
                print(f"  {sym}  {name}")
        print("-" * width)
        print(f"  Result : {overall}")
        print(f"  Passed : {passed}/{total}")
        if errors and (verbose or failed > 0):
            print()
            print("  Failures:")
            for e in errors:
                print(f"    ✗ {e}")
        print("=" * width)
        print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    args = _parse_args()
    sys.exit(run_health_check(verbose=args.verbose, json_output=args.json))
