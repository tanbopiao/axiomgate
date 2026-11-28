"""样例：三步走完公理裁决门最小闭环。

立公理 → 设裁决门 → 主张入门对册裁决，门簿留痕。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from axiomgate import AdjudicationGate, Axiom, AxiomRegistry, GateLedger


def main():
    # 一、立公理：两条不变量入册并封印
    registry = AxiomRegistry()
    registry.register(Axiom(
        "AX-NO-DELETE", "已确认记录不可删除",
        lambda claim: claim.get("action") != "delete_record"))
    registry.register(Axiom(
        "AX-SANITIZED", "对外发送必须先脱敏",
        lambda claim: not claim.get("action", "").startswith("send")
        or claim.get("sanitized") is True))
    for axiom in registry.axioms():
        registry.seal(axiom.axiom_id)

    # 二、设裁决门与门簿
    gate = AdjudicationGate(registry)
    ledger = GateLedger()

    # 三、主张入门：一条放行、一条被公理拦下
    claims = [
        {"action": "append_record", "note": "追加一条记录"},
        {"action": "send_report", "sanitized": False, "note": "未脱敏就外发"},
    ]
    for claim in claims:
        verdict = gate.adjudicate(claim)
        ledger.append(verdict)
        state = "放行" if verdict.approved else f"否决（违反 {verdict.violations}）"
        print(f"{claim['action']:<14} -> {state}")

    print(f"门簿 {len(ledger)} 条，链完整: {ledger.verify()}")


if __name__ == "__main__":
    main()
