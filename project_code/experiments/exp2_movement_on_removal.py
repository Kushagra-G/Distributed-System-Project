"""
"""

import csv
import os
import random
import string
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hash_ring import HashRing  # noqa: E402


N_PHYSICAL = 8
K_VALUES = [1, 2, 4, 8, 16, 32, 64, 128]
NUM_KEYS = 200_000
TRIALS = 5
NODE_TO_REMOVE = 3  # arbitrary; results are similar for any choice
OUT_PATH = os.path.join(os.path.dirname(__file__), "results_movement.csv")


def random_key(rng: random.Random, length: int = 16) -> str:
    return "".join(rng.choices(string.ascii_letters + string.digits, k=length))


def run_trial(k: int, num_keys: int, seed: int) -> float:
    rng = random.Random(seed)
    keys = [random_key(rng) for _ in range(num_keys)]

    ring = HashRing(physical_nodes=list(range(N_PHYSICAL)), k=k)
    before = [ring.get_node(key) for key in keys]

    ring.remove_node(NODE_TO_REMOVE)
    after = [ring.get_node(key) for key in keys]

    moved = sum(1 for b, a in zip(before, after) if b != a)
    return moved / num_keys


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["k", "trial", "fraction_moved", "n_physical", "num_keys"])
        for k in K_VALUES:
            for t in range(TRIALS):
                seed = 1000 * k + t
                frac = run_trial(k, NUM_KEYS, seed)
                w.writerow([k, t, f"{frac:.6f}", N_PHYSICAL, NUM_KEYS])
                print(f"K={k:>4d}  trial={t}  moved={frac:.4f}", flush=True)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
