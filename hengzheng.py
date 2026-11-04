"""心跳持续验证 —— 道统算子谱（hengzheng）
道统出处：恒久之证
工程映射：节点心跳与持续活性证明
生长纪律：本地生长自由，推送远端需治理决议发令。
"""
import json
import time

class Heartbeat:
    """心跳持续验证：beat 采集心跳，check 判活性，台账只增不覆盖。

    可选 ledger_path 传 jsonl 文件路径（每条心跳一行追加写）；不传则只记内存。
    """

    def __init__(self, ledger_path=None, now=None):
        self.ledger_path = ledger_path
        self._records = {}                   # {node: [(ts, note), ...]} 只增不覆盖
        self._now = now or time.time         # 可注入时钟，测试用

    def describe(self) -> dict:
        return {"name": "hengzheng", "role": "节点心跳与持续活性证明",
                "stage": "m1", "nodes": len(self._records)}

    def beat(self, node, note=""):
        """追加一跳：内存台账追加；有 ledger 时同步追加一行 jsonl。"""
        ts = self._now()
        self._records.setdefault(node, []).append((ts, note))
        if self.ledger_path:
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"node": node, "ts": ts, "note": note},
                                   ensure_ascii=False) + "\n")
        return ts

    def check(self, node, max_age_seconds=72 * 3600, now=None):
        """判活性：有跳且最新一跳在窗口内 → alive；超窗 → stale；无记录 → unknown。"""
        now_ts = now if now is not None else self._now()
        beats = self._records.get(node)
        if not beats:
            return "unknown"
        age = now_ts - max(b[0] for b in beats)
        return "alive" if age <= max_age_seconds else "stale"

    def stale_nodes(self, max_age_seconds=72 * 3600, now=None):
        """列出全部超窗节点（无记录的节点不在台账，不列入）。"""
        now_ts = now if now is not None else self._now()
        return sorted(n for n, beats in self._records.items()
                      if now_ts - max(b[0] for b in beats) > max_age_seconds)
