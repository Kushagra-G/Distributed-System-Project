# consistent hash ring with virtual nodes

import bisect
import hashlib
from typing import Dict, List


RING_BITS = 64
RING_SIZE = 1 << RING_BITS


def hash64(s: str) -> int:
    # sha1 truncated to 64 bits
    digest = hashlib.sha1(s.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


class HashRing:

    def __init__(self, physical_nodes: List[int], k: int = 1):
        if k < 1:
            raise ValueError("k must be >= 1")
        self.k = k
        self.physical_nodes: List[int] = list(physical_nodes)

        # positions and their owners are kept in sync
        self._positions: List[int] = []
        self._owners: List[int] = []

        for node_id in self.physical_nodes:
            self._add_node_unsorted(node_id)
        self._resort()

    def _vnode_position(self, node_id: int, j: int) -> int:
        return hash64(f"node-{node_id}-vnode-{j}")

    def _add_node_unsorted(self, node_id: int) -> None:
        for j in range(self.k):
            self._positions.append(self._vnode_position(node_id, j))
            self._owners.append(node_id)

    def _resort(self) -> None:
        paired = sorted(zip(self._positions, self._owners))
        self._positions = [p for p, _ in paired]
        self._owners = [o for _, o in paired]

    def add_node(self, node_id: int) -> None:
        if node_id in self.physical_nodes:
            return
        self.physical_nodes.append(node_id)
        self._add_node_unsorted(node_id)
        self._resort()

    def remove_node(self, node_id: int) -> None:
        if node_id not in self.physical_nodes:
            return
        self.physical_nodes.remove(node_id)
        kept = [
            (p, o) for p, o in zip(self._positions, self._owners) if o != node_id
        ]
        self._positions = [p for p, _ in kept]
        self._owners = [o for _, o in kept]

    def get_node(self, key: str) -> int:
        if not self._positions:
            raise RuntimeError("ring is empty")
        h = hash64(key)
        # wrap around if were past the last position
        idx = bisect.bisect_right(self._positions, h)
        if idx == len(self._positions):
            idx = 0
        return self._owners[idx]

    def distribute(self, keys) -> Dict[int, int]:
        counts: Dict[int, int] = {n: 0 for n in self.physical_nodes}
        for k in keys:
            counts[self.get_node(k)] += 1
        return counts

    def __len__(self) -> int:
        return len(self._positions)
