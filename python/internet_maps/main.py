import logging
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from sys import stderr, stdout
from typing import List
from uuid import UUID

import networkx as nx
import networkxtra as nxt
import typer
from pyasn import pyasn
from tqdm.auto import tqdm

from internet_maps.collectors import Collector
from internet_maps.loaders import (
    load_asn2info,
    load_asrel,
    load_assignments,
    load_origins,
)
from internet_maps.tree import make_tree
from internet_maps.utilities import closest_collector_date

app = typer.Typer()


@app.command("geojson")
def geojson(
    asn2info: str = typer.Option(
        "https://publicdata.caida.org/datasets/as-organizations/20220101.as-org2info.jsonl.gz"
    ),
    bgp_collector: str = typer.Option("rrc00.ripe.net"),
    bgp_date: datetime = typer.Option(datetime.utcnow(), help="UTC date"),
    ipv4_assignments: str = typer.Option(
        "https://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.csv"
    ),
    ipv6_assignments: str = typer.Option(
        "https://www.iana.org/assignments/ipv6-unicast-address-assignments/ipv6-unicast-address-assignments.csv"
    ),
    scale: int = typer.Option(1),
    edges: Path = typer.Argument(
        ..., exists=True, dir_okay=False, file_okay=True, readable=True
    ),
    layout: Path = typer.Argument(
        ..., exists=True, dir_okay=False, file_okay=True, readable=True
    ),
    output: Path = typer.Argument(..., dir_okay=False, file_okay=True, writable=True),
):
    # TODO: Take arbitrary networkx file as input? Or simple u,v file?
    bgp_date = closest_collector_date(bgp_date)
    assignments = load_assignments(ipv4_assignments, ipv6_assignments)
    asn2info = load_asn2info(asn2info)
    origins = load_origins(bgp_collector, bgp_date, print_progress=True)
    assignments_tree = make_tree(assignments)
    as_tree = make_tree(origins)
    graph = nxt.read_lgl(edges, create_using=nx.DiGraph)
    layout = nxt.lgl_layout_from_file(layout, scale)
    augment_graph(graph, assignments_tree, as_tree, asn2info)
    nxt.write_geojsonl(graph, layout, output)


def augment_graph(graph, assignments_tree, as_tree, asn2info):
    ndata = defaultdict(dict)
    for node in tqdm(graph.nodes, desc="Augmenting nodes"):
        # TODO: IX
        # TODO: near/far instead of u/v?
        asn = as_tree.get(node, "?")
        name, organization = asn2info.get(asn, ("?", "?"))
        ndata[node] = {
            "assignment": assignments_tree.get(node),
            "asn": asn,
            "as": name,
            "organization": organization,
            "title": node.replace("::ffff:", ""),
        }
    edata = {
        (u, v): {
            **{f"u_{k}": ndata[u][k] for k in ndata[u]},
            **{f"v_{k}": ndata[v][k] for k in ndata[v]},
        }
        for u, v in tqdm(graph.edges, desc="Augmenting edges")
    }
    nx.set_node_attributes(graph, ndata)
    nx.set_edge_attributes(graph, edata)
