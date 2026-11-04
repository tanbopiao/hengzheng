import json
import os
import tempfile
import unittest
from hengzheng import Heartbeat

class T(unittest.TestCase):
    def test_first_beat_alive(self):
        h = Heartbeat(now=lambda: 1000)
        h.beat("NODE-A")
        self.assertEqual(h.check("NODE-A", now=1100), "alive")
        self.assertEqual(h.check("NODE-A", now=1000 + 72 * 3600), "alive")  # 恰在窗口边缘

    def test_stale_beyond_window(self):
        h = Heartbeat(now=lambda: 1000)
        h.beat("NODE-A")
        self.assertEqual(h.check("NODE-A", now=1000 + 72 * 3600 + 1), "stale")

    def test_unknown_node(self):
        h = Heartbeat(now=lambda: 1000)
        self.assertEqual(h.check("没见过"), "unknown")

    def test_ledger_only_grows(self):
        """台账只增不覆盖：重复 beat 追加新行，旧记录永不被改写。"""
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        try:
            h = Heartbeat(ledger_path=path, now=lambda: 1000)
            h.beat("NODE-A", note="第一跳")
            h.beat("NODE-A", note="第二跳")
            lines = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
            self.assertEqual(len(lines), 2)                          # 两行都在
            self.assertEqual(lines[0]["note"], "第一跳")             # 旧记录原样保留
            self.assertEqual(lines[1]["note"], "第二跳")
            self.assertEqual(len(h._records["NODE-A"]), 2)           # 内存台账同样只增
        finally:
            os.unlink(path)

    def test_stale_nodes_listing(self):
        clock = [0]
        h = Heartbeat(now=lambda: clock[0])
        h.beat("快节点")
        clock[0] = 1000 + 72 * 3600
        h.beat("慢节点")
        out = h.stale_nodes(now=1000 + 72 * 3600 + 5)
        self.assertEqual(out, ["快节点"])   # 旧跳超窗；慢节点刚跳过故新鲜

    def test_latest_beat_refreshes_liveness(self):
        h = Heartbeat(now=lambda: 0)
        h.beat("NODE-A")
        h = Heartbeat(now=lambda: 10)
        h._records = {"NODE-A": [(0, ""), (10, "")]}                 # 复现两次跳动
        self.assertEqual(h.check("NODE-A", max_age_seconds=5, now=12), "alive")

if __name__ == "__main__":
    unittest.main()
