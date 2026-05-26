# dis-sys-project-

This project extends the distributed key-value store from class with consistent hashing and virtual nodes, and looks at how the load imbalance changes as you crank up the number of virtual nodes per physical node. The ring lives in hash_ring.py as a sorted list of positions with a bisect lookup, keys and vnodes both get hashed with SHA-1 truncated to 64 bits (same convention as dsutils.str_to_id), and vnode positions are derived determnistically from the node name so the ring rebuilds the same way every run. The Flask service in node.py wraps the ring so each pod can route requests to whoever actually owns the key. K is set with the VNODE_K env var.

I ran two experiments, both with 8 physical nodes and K swept across {1, 2, 4, 8, 16, 32, 64, 128}. The first hashes 1M random keys per trial and tracks the coeficient of variation of per node key counts across 10 trials per K the log-log fit comes out at a slope between -0.45 and -0.55, which lines up with the O(1/rootK) predction. The second hashes 200k keys per trial across 5 trials per K, removes one node, and measures what fraction of keys had to move, that is right around 0.125 across all K values, which matches the 1/N expectation for N=8. So both the imbalance scaling and the movement bound came out close to 
theory, which was the main thing I wanted to confirm.

## Run it
Make sure to be in the project_code directory


```bash
cd project_code 
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt

make test       # 10 unit tests, 1 sec
make exp1       # load variance sweep, about 5 min
make exp2       # key movement on node removal, about 1 min
make plots      # writes plots/cov_vs_k.png and plots/movement.png
```

Or all of the above in one shot-

```bash
make all
```

## Expected results

- `plots/cov_vs_k.png` — log-log fit slope between **−0.45 and −0.55** (theory: −0.5)
- `plots/movement.png` — fraction moved ≈ **0.125 ± 0.02** for all K (theory: 1/N = 0.125)

## If `make` fails with `python: No such file or directory`

Either run `source .venv/bin/activate` first, or:

```bash
sed -i '' 's/python /python3 /g' Makefile   # macOS
sed -i 's/python /python3 /g' Makefile      # Linux
```

