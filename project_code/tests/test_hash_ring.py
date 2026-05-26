"""
Sanity tests for HashRing. Run with: python -m pytest tests/ -v
or just: python tests/test_hash_ring.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hash_ring import HashRing, hash64  # noqa: E402


class TestHashRing(unittest.TestCase):

    def test_hash64_deterministic(self):
        self.assertEqual(hash64("hello"), hash64("hello"))
        self.assertNotEqual(hash64("hello"), hash64("world"))
        self.assertTrue(0 <= hash64("x") < (1 << 64))

    def test_ring_size(self):
        ring = HashRing(physical_nodes=[0, 1, 2, 3], k=10)
        self.assertEqual(len(ring), 40)

    def test_routing_deterministic(self):
        ring1 = HashRing(physical_nodes=[0, 1, 2, 3], k=8)
        ring2 = HashRing(physical_nodes=[0, 1, 2, 3], k=8)
        for key in ["alpha", "beta", "gamma", "delta", "epsilon"]:
            self.assertEqual(ring1.get_node(key), ring2.get_node(key))

    def test_routing_returns_valid_node(self):
        nodes = [0, 1, 2, 3, 4, 5, 6, 7]
        ring = HashRing(physical_nodes=nodes, k=16)
        for i in range(1000):
            owner = ring.get_node(f"key-{i}")
            self.assertIn(owner, nodes)

    def test_distribute_counts_sum_correctly(self):
        ring = HashRing(physical_nodes=[0, 1, 2, 3], k=32)
        keys = [f"k{i}" for i in range(10_000)]
        counts = ring.distribute(keys)
        self.assertEqual(sum(counts.values()), 10_000)

    def test_more_vnodes_lowers_variance(self):
        """Higher K should give lower CoV in expectation."""
        import random
        import statistics
        rng = random.Random(42)
        keys = [str(rng.random()) for _ in range(100_000)]

        def cov(k):
            ring = HashRing(physical_nodes=list(range(8)), k=k)
            counts = ring.distribute(keys)
            vals = list(counts.values())
            return statistics.pstdev(vals) / statistics.mean(vals)

        cov_low = cov(1)
        cov_high = cov(64)
        self.assertGreater(cov_low, cov_high)

    def test_remove_node_moves_about_one_over_n(self):
        nodes = [0, 1, 2, 3, 4, 5, 6, 7]
        ring = HashRing(physical_nodes=nodes, k=64)
        keys = [f"key-{i}" for i in range(50_000)]
        before = [ring.get_node(k) for k in keys]
        ring.remove_node(3)
        after = [ring.get_node(k) for k in keys]
        moved = sum(1 for b, a in zip(before, after) if b != a)
        frac = moved / len(keys)
        # 1/8 = 0.125; allow a generous window for randomness.
        self.assertGreater(frac, 0.08)
        self.assertLess(frac, 0.18)

    def test_add_node_is_inverse_of_remove(self):
        ring = HashRing(physical_nodes=[0, 1, 2, 3], k=8)
        before = [ring.get_node(f"k{i}") for i in range(500)]
        ring.add_node(4)
        ring.remove_node(4)
        after = [ring.get_node(f"k{i}") for i in range(500)]
        self.assertEqual(before, after)

    def test_empty_ring_raises(self):
        ring = HashRing(physical_nodes=[0], k=1)
        ring.remove_node(0)
        with self.assertRaises(RuntimeError):
            ring.get_node("anything")

    def test_invalid_k(self):
        with self.assertRaises(ValueError):
            HashRing(physical_nodes=[0, 1], k=0)


if __name__ == "__main__":
    unittest.main()
