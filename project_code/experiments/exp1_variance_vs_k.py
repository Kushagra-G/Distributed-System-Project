"""

"""

import csv
import os
import random
import statistics
import string
import sys

# Make src importable when running from project root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from hash_ring import HashRing  # noqa: E402


N_PHYSICAL = 8
K_VALUES = [1, 2, 4, 8, 16, 32, 64, 128]
NUM_KEYS = 1_000_000
TRIALS = 10
OUT_PATH = os.path.join(os.path.dirname(__file__), "results_variance.csv")


def random_key(rng: random.Random, length: int = 16) -> str:
    return "".join(rng.choices(string.ascii_letters + string.digits, k=length))


def run_trial(k: int, num_keys: int, seed: int) -> float:
    rng = random.Random(seed)
    ring = HashRing(physical_nodes=list(range(N_PHYSICAL)), k=k)
    keys = (random_key(rng) for _ in range(num_keys))
    counts = ring.distribute(keys)
    values = list(counts.values())
    mean = statistics.mean(values)
    stdev = statistics.pstdev(values)  # population stdev across nodes
    return stdev / mean if mean > 0 else 0.0


def main():
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["k", "trial", "cov", "n_physical", "num_keys"])
        for k in K_VALUES:
            for t in range(TRIALS):
                seed = 1000 * k + t
                cov = run_trial(k, NUM_KEYS, seed)
                w.writerow([k, t, f"{cov:.6f}", N_PHYSICAL, NUM_KEYS])
                print(f"K={k:>4d}  trial={t}  CoV={cov:.4f}", flush=True)
    print(f"\nWrote {OUT_PATH}")


if __name__ == "__main__":
    main()
