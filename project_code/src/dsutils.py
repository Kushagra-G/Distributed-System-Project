# hashing utils shared with the original KV store

import hashlib


def str_to_id(s: str) -> int:
    digest = hashlib.sha1(s.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")
