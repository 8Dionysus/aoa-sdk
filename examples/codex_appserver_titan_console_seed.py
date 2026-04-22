#!/usr/bin/env python3
"""Codex app-server Titan console seed.

This script is a minimal JSONL client skeleton. It starts `codex app-server`,
initializes a thread, and sends the Titan runtime harness summon prompt.

It is intentionally a seed, not a production console.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import threading
from pathlib import Path


DEFAULT_PROMPT = """Spawn Atlas, Sentinel, and Mneme as the Titan service cohort.
Keep Forge locked until mutation gate.
Keep Delta locked until judgment gate.
Return roster, route frame, risk gates, and receipt posture.
"""


def emit(proc: subprocess.Popen, message: dict) -> None:
    line = json.dumps(message, ensure_ascii=False)
    assert proc.stdin is not None
    proc.stdin.write(line + "\n")
    proc.stdin.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description="Titan console seed for Codex app-server")
    parser.add_argument("--cwd", default="/srv")
    parser.add_argument("--model", default="gpt-5.4")
    parser.add_argument("--prompt-file")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    prompt = DEFAULT_PROMPT
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")

    messages = [
        {
            "method": "initialize",
            "id": 0,
            "params": {"clientInfo": {"name": "aoa_titan_console_seed", "title": "AoA Titan Console Seed", "version": "0.1.0"}},
        },
        {"method": "initialized", "params": {}},
        {
            "method": "thread/start",
            "id": 1,
            "params": {"model": args.model, "cwd": args.cwd, "serviceName": "aoa_titan_console_seed"},
        },
    ]

    if args.dry_run:
        for message in messages:
            print(json.dumps(message, indent=2, ensure_ascii=False))
        print("TURN_PROMPT:")
        print(prompt)
        return 0

    proc = subprocess.Popen(["codex", "app-server"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr, text=True)
    thread_id = {"value": None}

    def reader() -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            print("server:", line.rstrip())
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            if msg.get("id") == 1 and msg.get("result", {}).get("thread", {}).get("id"):
                thread_id["value"] = msg["result"]["thread"]["id"]
                emit(proc, {
                    "method": "turn/start",
                    "id": 2,
                    "params": {
                        "threadId": thread_id["value"],
                        "input": [{"type": "text", "text": prompt}]
                    }
                })

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()

    for message in messages:
        emit(proc, message)

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    return proc.returncode or 0


if __name__ == "__main__":
    raise SystemExit(main())
