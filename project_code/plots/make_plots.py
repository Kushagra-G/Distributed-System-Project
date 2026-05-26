"""
Generate the two plots

  1. plots/cov_vs_k.png  -- log-log of CoV vs K with theoretical
                            1/sqrt(K) reference line and a least-squares
                            fit. Includes error bars (mean +/- stdev
                            across trials).
  2. plots/movement.png  -- fraction of keys moved on node removal vs K,
                            with the 1/N reference line.

                            mathy stuff
"""


import csv
import math
import os
import statistics
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np


HERE = os.path.dirname(__file__)
EXP_DIR = os.path.join(HERE, "..", "experiments")
PLOT_DIR = os.path.join(HERE)


def load_csv(path: str):
    with open(path, "r", newline="") as f:
        r = csv.DictReader(f)
        return list(r)


def plot_cov_vs_k():
    rows = load_csv(os.path.join(EXP_DIR, "results_variance.csv"))
    by_k = defaultdict(list)
    for row in rows:
        by_k[int(row["k"])].append(float(row["cov"]))
    n_physical = int(rows[0]["n_physical"])

    ks = sorted(by_k.keys())
    means = [statistics.mean(by_k[k]) for k in ks]
    stds = [statistics.pstdev(by_k[k]) for k in ks]

    # Least-squares fit on log-log: log(cov) = a + b*log(k); expect b ~ -0.5.
    logk = np.log(ks)
    logc = np.log(means)
    slope, intercept = np.polyfit(logk, logc, 1)
    fit = np.exp(intercept) * np.array(ks, dtype=float) ** slope

    # Theoretical 1/sqrt(k) reference, anchored at K=1 mean.
    theory = means[0] / np.sqrt(np.array(ks, dtype=float))

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.errorbar(ks, means, yerr=stds, fmt="o", label="Measured CoV", capsize=3)
    ax.plot(ks, fit, "--", label=f"Fit: slope = {slope:.3f}")
    ax.plot(ks, theory, ":", label="Theory: $1/\\sqrt{K}$")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("K (virtual nodes per physical node)")
    ax.set_ylabel("Coefficient of variation (stdev / mean)")
    ax.set_title(f"Load variance vs K  (N = {n_physical} physical nodes)")
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    out = os.path.join(PLOT_DIR, "cov_vs_k.png")
    fig.savefig(out, dpi=150)
    print(f"Wrote {out}  (fit slope = {slope:.3f}, expected ~-0.5)")


def plot_movement():
    rows = load_csv(os.path.join(EXP_DIR, "results_movement.csv"))
    by_k = defaultdict(list)
    for row in rows:
        by_k[int(row["k"])].append(float(row["fraction_moved"]))
    n_physical = int(rows[0]["n_physical"])

    ks = sorted(by_k.keys())
    means = [statistics.mean(by_k[k]) for k in ks]
    stds = [statistics.pstdev(by_k[k]) for k in ks]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.errorbar(ks, means, yerr=stds, fmt="o", label="Measured", capsize=3)
    ax.axhline(1.0 / n_physical, linestyle="--",
               label=f"Theory: 1/N = {1.0/n_physical:.3f}")
    ax.set_xscale("log")
    ax.set_xlabel("K (virtual nodes per physical node)")
    ax.set_ylabel("Fraction of keys moved")
    ax.set_title(f"Key movement on node removal  (N = {n_physical})")
    ax.set_ylim(0, max(means) * 1.5 + 0.05)
    ax.grid(True, which="both", linestyle=":", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    out = os.path.join(PLOT_DIR, "movement.png")
    fig.savefig(out, dpi=150)
    print(f"Wrote {out}")


if __name__ == "__main__":
    plot_cov_vs_k()
    plot_movement()
