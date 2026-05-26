"""
Distributed KV node, extended to use a consistent hash ring with
virtual nodes. Drop-in replacement for the original dspy-node service.

New behavior:
  - Routing is done via HashRing instead of `hash % NUM_NODES`.
  - Each node holds a local in-memory store; PUT/GET forward to the
    correct owner if the key doesn't belong here.
  - `K` (vnodes per physical node) is configurable via env var VNODE_K.

Endpoints:
  GET  /                  hello
  GET  /host              hostname
  GET  /ping              pong
  GET  /hash/<key>        raw hash of key
  GET  /node/<key>        which physical node owns this key
  GET  /kv/<key>          fetch (forwards if not local)
  PUT  /kv/<key>          store (forwards if not local), body = value
  GET  /local             dump this node's local store (for debugging)
  GET  /peers             ping every peer
"""

import os
import socket
import threading

import requests
from flask import Flask, jsonify, request

from dsutils import str_to_id
from hash_ring import HashRing


# ---------- config ----------
NUM_NODES = int(os.environ.get("NUM_NODES", "8"))
PORT = int(os.environ.get("PORT", "5000"))
SVC_DOMAIN = os.environ.get("SVC_DOMAIN", "dspy-svc.default.svc.cluster.local")
VNODE_K = int(os.environ.get("VNODE_K", "64"))


def own_node_id() -> int:
    hostname = socket.gethostname()  # e.g. "dspy-node-2"
    return int(hostname.split("-")[-1])


def host_for(node_id: int) -> str:
    return f"dspy-node-{node_id}.{SVC_DOMAIN}"


def url_for(node_id: int) -> str:
    return f"http://{host_for(node_id)}:{PORT}"


def peer_ids():
    me = own_node_id()
    return [i for i in range(NUM_NODES) if i != me]


# ---------- state ----------
app = Flask(__name__)
ring = HashRing(physical_nodes=list(range(NUM_NODES)), k=VNODE_K)
_store_lock = threading.Lock()
_store: dict = {}


# ---------- basic endpoints ----------
@app.route("/")
def hello():
    return f"Hello from {socket.gethostname()} (K={VNODE_K})\n"


@app.route("/host")
def host():
    return socket.gethostname() + "\n"


@app.route("/ping")
def ping():
    return f"pong from {socket.gethostname()}\n"


@app.route("/hash/<key>")
def hash_key(key):
    return str(str_to_id(key)) + "\n"


@app.route("/node/<key>")
def node_for_key(key):
    owner = ring.get_node(key)
    return (
        f"key={key} hash={str_to_id(key)} node={owner} "
        f"host={host_for(owner)}\n"
    )


# ---------- KV with forwarding ----------
@app.route("/kv/<key>", methods=["GET"])
def kv_get(key):
    owner = ring.get_node(key)
    if owner == own_node_id():
        with _store_lock:
            val = _store.get(key)
        if val is None:
            return ("not found\n", 404)
        return val + "\n"
    # forward
    try:
        r = requests.get(f"{url_for(owner)}/kv/{key}", timeout=2)
        return (r.text, r.status_code)
    except Exception as e:
        return (f"forward error: {e}\n", 502)


@app.route("/kv/<key>", methods=["PUT"])
def kv_put(key):
    value = request.get_data(as_text=True)
    owner = ring.get_node(key)
    if owner == own_node_id():
        with _store_lock:
            _store[key] = value
        return "stored locally\n"
    try:
        r = requests.put(f"{url_for(owner)}/kv/{key}", data=value, timeout=2)
        return (r.text, r.status_code)
    except Exception as e:
        return (f"forward error: {e}\n", 502)


@app.route("/local")
def local_dump():
    with _store_lock:
        return jsonify({"node": own_node_id(), "count": len(_store)})


@app.route("/peers")
def peers():
    results = {}
    for pid in peer_ids():
        u = url_for(pid)
        try:
            r = requests.get(f"{u}/ping", timeout=2)
            results[u] = r.text.strip()
        except Exception as e:
            results[u] = f"ERROR: {e}"
    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
