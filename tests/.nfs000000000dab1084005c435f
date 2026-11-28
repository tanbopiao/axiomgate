"""公理裁决门五域回归套件（纯标准库，干净环境可跑）。

运行：python -m unittest discover -s tests -v
铁律见 tests/regression.md。
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from axiomgate import (  # noqa: E402
    AdjudicationGate,
    Axiom,
    AxiomRegistry,
    DuplicateAxiomError,
    GateLedger,
    InvalidClaimError,
    SealedAxiomError,
    UnknownAxiomError,
    selftest,
)


def make_registry():
    reg = AxiomRegistry()
    reg.register(Axiom("AX-01", "已确认记录不可删除",
                       lambda c: c.get("action") != "delete_record"))
    reg.register(Axiom("AX-02", "对外发送须先脱敏",
                       lambda c: not c.get("action", "").startswith("send")
                       or c.get("sanitized") is True))
    return reg


class TestRegistryDomain(unittest.TestCase):
    """域一：公理册。"""

    def test_register_and_len(self):
        reg = make_registry()
        self.assertEqual(len(reg), 2)

    def test_duplicate_rejected(self):
        reg = make_registry()
        with self.assertRaises(DuplicateAxiomError):
            reg.register(Axiom("AX-01", "重复入册", lambda c: True))

    def test_invalid_axiom_rejected(self):
        reg = AxiomRegistry()
        with self.assertRaises(InvalidClaimError):
            reg.register(Axiom("", "空编号", lambda c: True))
        with self.assertRaises(InvalidClaimError):
            reg.register(Axiom("AX-X", "谓词不可调用", None))

    def test_seal_prevents_unregister(self):
        reg = make_registry()
        reg.seal("AX-01")
        with self.assertRaises(SealedAxiomError):
            reg.unregister("AX-01")

    def test_unregister_unsealed(self):
        reg = make_registry()
        reg.unregister("AX-02")
        self.assertEqual(len(reg), 1)

    def test_unknown_axiom(self):
        reg = AxiomRegistry()
        with self.assertRaises(UnknownAxiomError):
            reg.get("AX-404")

    def test_axioms_sorted_order(self):
        reg = AxiomRegistry()
        reg.register(Axiom("AX-B", "后入", lambda c: True))
        reg.register(Axiom("AX-A", "先入", lambda c: True))
        self.assertEqual([a.axiom_id for a in reg.axioms()], ["AX-A", "AX-B"])


class TestGateDomain(unittest.TestCase):
    """域二：裁决门。"""

    def test_approve_when_all_hold(self):
        gate = AdjudicationGate(make_registry())
        v = gate.adjudicate({"action": "append_record"})
        self.assertTrue(v.approved)
        self.assertEqual(v.checked, ["AX-01", "AX-02"])

    def test_veto_on_violation(self):
        gate = AdjudicationGate(make_registry())
        v = gate.adjudicate({"action": "delete_record"})
        self.assertFalse(v.approved)
        self.assertEqual(v.violations, ["AX-01"])

    def test_veto_lists_all_violations(self):
        gate = AdjudicationGate(make_registry())
        v = gate.adjudicate({"action": "send_mail", "sanitized": False})
        self.assertFalse(v.approved)
        self.assertEqual(v.violations, ["AX-02"])

    def test_out_of_register_claim_rejected(self):
        gate = AdjudicationGate(make_registry())
        with self.assertRaises(InvalidClaimError):
            gate.adjudicate({"action": ""})
        with self.assertRaises(InvalidClaimError):
            gate.adjudicate("不是 dict")

    def test_digest_deterministic(self):
        gate = AdjudicationGate(make_registry())
        v1 = gate.adjudicate({"action": "append_record"})
        v2 = gate.adjudicate({"action": "append_record"})
        self.assertEqual(v1.digest, v2.digest)

    def test_adjudicate_many(self):
        gate = AdjudicationGate(make_registry())
        results = gate.adjudicate_many([
            {"action": "append_record"},
            {"action": "delete_record"},
        ])
        self.assertEqual([r.approved for r in results], [True, False])


class TestLedgerDomain(unittest.TestCase):
    """域三：门簿哈希链。"""

    def _filled_ledger(self, n=3):
        gate = AdjudicationGate(make_registry())
        ledger = GateLedger()
        for i in range(n):
            ledger.append(gate.adjudicate({"action": f"act_{i}"}))
        return ledger

    def test_append_chain(self):
        ledger = self._filled_ledger()
        self.assertEqual(len(ledger), 3)
        recs = ledger.records()
        self.assertEqual([r["seq"] for r in recs], [1, 2, 3])
        self.assertTrue(all(recs[i]["hash"] == recs[i + 1]["prev"]
                            for i in range(len(recs) - 1)))

    def test_verify_clean(self):
        self.assertTrue(self._filled_ledger().verify())

    def test_verify_detects_tamper(self):
        ledger = self._filled_ledger()
        recs = ledger.records()
        recs[1]["verdict"]["approved"] = not recs[1]["verdict"]["approved"]
        self.assertFalse(ledger.verify())

    def test_genesis_prev_zero(self):
        ledger = self._filled_ledger(1)
        self.assertEqual(ledger.records()[0]["prev"], "0" * 64)


class TestSelftestDomain(unittest.TestCase):
    """域四：内嵌自测与样例。"""

    def test_embedded_selftest(self):
        self.assertTrue(selftest())

    def test_example_flow(self):
        example = Path(__file__).resolve().parent.parent / "examples" / "example.py"
        self.assertTrue(example.exists(), "examples/example.py 应存在")


class TestMappingDomain(unittest.TestCase):
    """域五：道统映射一致性。"""

    def test_naming_semantics_in_module(self):
        import axiomgate as m
        self.assertIn("公理裁决门", m.__doc__)
        self.assertIn("命名即种子", m.__doc__)

    def test_readme_mapping_table(self):
        readme = (Path(__file__).resolve().parent.parent / "README.md").read_text(
            encoding="utf-8")
        for kw in ["道统映射", "公理册", "裁决门", "门簿"]:
            self.assertIn(kw, readme)


if __name__ == "__main__":
    unittest.main()
