"""axiomgate — 公理裁决门：不变量注册与裁决门内核。

命名即种子：公理裁决门＝先立公理（不变量）入册封印，后凡入门之主张
皆对册裁决；门内只认已注册的公理，册外主张一律不放行。

逻辑本体：公理（不变量）→ 公理册（注册与封印）→ 裁决门（对册裁决）
→ 门簿（裁决留痕、哈希链防篡改）。

纯标准库实现，Python >= 3.10。
"""

from __future__ import annotations

import hashlib
import json
import time

__all__ = [
    "Axiom",
    "AxiomRegistry",
    "AdjudicationGate",
    "GateLedger",
    "Verdict",
    "DuplicateAxiomError",
    "UnknownAxiomError",
    "SealedAxiomError",
    "InvalidClaimError",
    "selftest",
]

_VERSION = "0.1.0"


class DuplicateAxiomError(ValueError):
    """公理册中已存在同号公理。"""


class UnknownAxiomError(KeyError):
    """公理册中不存在该编号。"""


class SealedAxiomError(PermissionError):
    """公理已封印，不可除名或改写。"""


class InvalidClaimError(ValueError):
    """主张不合法：缺少必要字段或类型不符。"""


class Axiom:
    """一条公理（不变量）：编号、陈述与判定谓词。

    predicate 接收主张 dict，返回 True 表示主张不违反该公理。
    """

    def __init__(self, axiom_id: str, statement: str, predicate):
        if not axiom_id or not isinstance(axiom_id, str):
            raise InvalidClaimError("axiom_id 必须是非空字符串")
        if not statement or not isinstance(statement, str):
            raise InvalidClaimError("statement 必须是非空字符串")
        if not callable(predicate):
            raise InvalidClaimError("predicate 必须可调用")
        self.axiom_id = axiom_id
        self.statement = statement
        self.predicate = predicate
        self.sealed = False

    def holds(self, claim: dict) -> bool:
        """判定主张是否不违反本公理。"""
        return bool(self.predicate(claim))

    def to_dict(self) -> dict:
        return {"axiom_id": self.axiom_id, "statement": self.statement,
                "sealed": self.sealed}


class AxiomRegistry:
    """公理册：公理的注册、封印与查询。

    封印（seal）体现不变量语义：入册封印后的公理不可除名——
    不变量之所以为不变量，在于它不随主张的改变而改变。
    """

    def __init__(self):
        self._axioms: dict[str, Axiom] = {}

    def register(self, axiom: Axiom) -> Axiom:
        if axiom.axiom_id in self._axioms:
            raise DuplicateAxiomError(f"公理已入册: {axiom.axiom_id}")
        self._axioms[axiom.axiom_id] = axiom
        return axiom

    def unregister(self, axiom_id: str) -> None:
        axiom = self._axioms.get(axiom_id)
        if axiom is None:
            raise UnknownAxiomError(axiom_id)
        if axiom.sealed:
            raise SealedAxiomError(f"公理已封印，不可除名: {axiom_id}")
        del self._axioms[axiom_id]

    def seal(self, axiom_id: str) -> None:
        axiom = self._axioms.get(axiom_id)
        if axiom is None:
            raise UnknownAxiomError(axiom_id)
        axiom.sealed = True

    def get(self, axiom_id: str) -> Axiom:
        axiom = self._axioms.get(axiom_id)
        if axiom is None:
            raise UnknownAxiomError(axiom_id)
        return axiom

    def axioms(self) -> tuple:
        """按编号排序返回全部公理（裁决顺序确定）。"""
        return tuple(self._axioms[k] for k in sorted(self._axioms))

    def __len__(self) -> int:
        return len(self._axioms)


class Verdict:
    """一次裁决的结论：放行与否、对过哪些公理、违反了哪些。"""

    def __init__(self, claim_id: str, approved: bool, checked: list,
                 violations: list, taken_at: float, digest: str):
        self.claim_id = claim_id
        self.approved = approved
        self.checked = list(checked)
        self.violations = list(violations)
        self.taken_at = taken_at
        self.digest = digest

    def to_dict(self) -> dict:
        return {"claim_id": self.claim_id, "approved": self.approved,
                "checked": list(self.checked), "violations": list(self.violations),
                "taken_at": self.taken_at, "digest": self.digest}


def _canonical(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _digest(obj) -> str:
    return hashlib.sha256(_canonical(obj).encode("utf-8")).hexdigest()


class AdjudicationGate:
    """裁决门：凡入门主张，逐条对册裁决。

    裁决规则：
    - 主张必须是含非空 action 字段的 dict（册外形态不入门）；
    - 主张逐条过全部已注册公理，全过则放行；
    - 任一公理判假即否决，并列出违反的公理编号；
    - 每次裁决产出确定性摘要（同主张同册同摘要），供门簿留痕。
    """

    def __init__(self, registry: AxiomRegistry):
        self.registry = registry

    def adjudicate(self, claim: dict, claim_id: str | None = None) -> Verdict:
        if not isinstance(claim, dict):
            raise InvalidClaimError("主张必须是 dict")
        action = claim.get("action")
        if not action or not isinstance(action, str):
            raise InvalidClaimError("主张缺少非空 action 字段（册外形态不入门）")
        taken_at = time.time()
        checked: list = []
        violations: list = []
        for axiom in self.registry.axioms():
            checked.append(axiom.axiom_id)
            if not axiom.holds(claim):
                violations.append(axiom.axiom_id)
        approved = not violations
        digest = _digest({"action": action, "checked": checked,
                          "violations": violations, "approved": approved})
        return Verdict(claim_id or action, approved, checked, violations,
                       taken_at, digest)

    def adjudicate_many(self, claims) -> list:
        return [self.adjudicate(c) for c in claims]


class GateLedger:
    """门簿：裁决记录的哈希链留痕，防篡改、可回放。"""

    def __init__(self):
        self._records: list = []
        self._prev = "0" * 64

    def append(self, verdict: Verdict) -> dict:
        record = {"seq": len(self._records) + 1, "verdict": verdict.to_dict(),
                  "prev": self._prev}
        record["hash"] = _digest({"seq": record["seq"], "verdict": record["verdict"],
                                  "prev": record["prev"]})
        self._records.append(record)
        self._prev = record["hash"]
        return dict(record)

    def verify(self) -> bool:
        """复核全链：任一环哈希对不上即判篡改。"""
        prev = "0" * 64
        for rec in self._records:
            expect = _digest({"seq": rec["seq"], "verdict": rec["verdict"],
                              "prev": prev})
            if rec["prev"] != prev or rec["hash"] != expect:
                return False
            prev = rec["hash"]
        return True

    def records(self) -> tuple:
        return tuple(self._records)

    def __len__(self) -> int:
        return len(self._records)


def selftest():
    """内嵌自测：最小闭环冒烟（完整回归见 tests/）。"""
    reg = AxiomRegistry()
    reg.register(Axiom("AX-NO-DELETE", "已确认记录不可删除",
                       lambda c: c.get("action") != "delete_record"))
    reg.seal("AX-NO-DELETE")
    gate = AdjudicationGate(reg)
    ok = gate.adjudicate({"action": "append_record"})
    bad = gate.adjudicate({"action": "delete_record"})
    assert ok.approved and not ok.violations
    assert not bad.approved and bad.violations == ["AX-NO-DELETE"]
    ledger = GateLedger()
    ledger.append(ok)
    ledger.append(bad)
    assert ledger.verify()
    assert len(ledger) == 2
    return True


if __name__ == "__main__":
    selftest()
    print(f"axiomgate {_VERSION} selftest OK")
