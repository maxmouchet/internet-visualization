from typing import Any

from pytricia import PyTricia
from tqdm import tqdm


def make_tree(mapping: dict[str, Any]) -> PyTricia:
    tree = PyTricia(128)
    for prefix, data in tqdm(mapping.items(), desc="make_tree"):
        if "." in prefix and not prefix.startswith("::ffff:"):
            address, size = prefix.split("/")
            prefix = f"::ffff:{address}/{96 + int(size)}"
        tree[prefix] = data
    return tree
