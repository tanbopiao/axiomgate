#!/usr/bin/env python3
"""命令行裁决小工具：用 JSON 主张过一遍公理裁决门。

用法：
    python tools/adjudicate.py '{"action": "append_record"}'
    echo '{"action": "send_report", "sanitized": false}' | python tools/adjudicate.py

内置演示公理册（AX-NO-DELETE / AX-SANITIZED）。
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from axiomgate import AdjudicationGate, Axiom, AxiomRegistry, GateLedger  # noqa: E402


def demo_registry():
    reg = AxiomRegistry()
    reg.register(Axiom("AX-NO-DELETE", "已确认记录不可删除",
                       lambda c: c.get("action") != "delete_record"))
    reg.register(Axiom("AX-SANITIZED", "对外发送必须先脱敏",
                       lambda c: not c.get("action", "").startswith("send")
                       or c.get("sanitized") is True))
    return reg


def main():
    raw = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    try:
        claim = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"主张不是合法 JSON: {exc}", file=sys.stderr)
        return 2
    gate = AdjudicationGate(demo_registry())
    try:
        verdict = gate.adjudicate(claim)
    except Exception as exc:  # InvalidClaimError 等
        print(f"裁决拒绝：{exc}", file=sys.stderr)
        return 2
    ledger = GateLedger()
    ledger.append(verdict)
    print(json.dumps({"approved": verdict.approved,
                      "violations": verdict.violations,
                      "digest": verdict.digest,
                      "ledger_verified": ledger.verify()},
                     ensure_ascii=False))
    return 0 if verdict.approved else 1


if __name__ == "__main__":
    sys.exit(main())
