# axiomgate

公理裁决门 · 不变量注册与裁决门内核 ｜元枢体系 YUANSHU

先立公理（不变量）入册封印，后凡入门之主张皆对册裁决——门内只认已注册的公理，册外主张一律不放行，每次裁决在门簿留痕、哈希链防篡改。

## 道统映射（命名即种子）

| 名 | 逻辑本体 | 架构落位 | 算子 |
|---|---|---|---|
| 公理 | 不变量：所有变化里不动的那个 | `Axiom`（编号＋陈述＋判定谓词，可封印） | `holds(claim)` |
| 公理册 | 立标：先立不变量，后谈裁决 | `AxiomRegistry`（注册／封印／查询） | `register / seal / axioms` |
| 裁决门 | 对册裁决：册外不入门 | `AdjudicationGate`（逐条对册、确定性摘要） | `adjudicate / adjudicate_many` |
| 门簿 | 留痕可溯：裁决不因时间失忆 | `GateLedger`（哈希链、防篡改复核） | `append / verify` |

## 快速开始

```python
from axiomgate import AdjudicationGate, Axiom, AxiomRegistry, GateLedger

registry = AxiomRegistry()
registry.register(Axiom("AX-NO-DELETE", "已确认记录不可删除",
                        lambda c: c.get("action") != "delete_record"))
registry.seal("AX-NO-DELETE")

gate = AdjudicationGate(registry)
verdict = gate.adjudicate({"action": "append_record"})
print(verdict.approved)   # True

ledger = GateLedger()
ledger.append(verdict)
print(ledger.verify())    # True
```

命令行：

```bash
python tools/adjudicate.py '{"action": "delete_record"}'   # 退出码 1，输出违反公理
python examples/example.py                                  # 最小闭环演示
```

## 设计约定

- **封印即不变**：入册封印的公理不可除名——不变量之所以为不变量，在于它不随主张的改变而改变。
- **册外不入门**：主张必须是含非空 `action` 的 dict，否则直接拒绝，不进裁决。
- **确定性摘要**：同主张同册必得同摘要，门簿据此对账；裁决过程不引入随机因素。
- **纯标准库**：Python ≥ 3.10，零第三方依赖，干净环境可跑全部回归。

## 回归

```bash
python -m unittest discover -s tests -v
```

五域用例：公理册（7）／裁决门（6）／门簿（4）／自测与样例（2）／道统映射（2）。铁律见 `tests/regression.md`。

## 许可证

MIT
