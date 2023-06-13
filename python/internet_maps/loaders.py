import json
import os
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import fsspec
import pandas as pd
from appdirs import user_cache_dir
from joblib import Memory
from pyasn import mrtx, pyasn

from internet_maps.collectors import Collector

memory = Memory(user_cache_dir("internet-maps", "maxmouchet"), verbose=2)


@memory.cache
def load_asrel(filename: str) -> set[tuple[int, int]]:
    # TODO: Directionality?
    as_rel = set()
    with fsspec.open(filename, "rt", compression="infer") as f:
        for line in f:
            if line.startswith("#"):
                continue
            a, b, _, _ = line.split("|")
            as_rel.add((int(a), int(b)))
    return as_rel


@memory.cache
def load_assignments(ipv4_filename: str, ipv6_filename: str) -> dict[str, str]:
    assignments = {}
    df = pd.read_csv(ipv4_filename)
    for row in df.itertuples():
        designation = row.Designation.replace("Administered by ", "")
        prefix = row.Prefix
        assert prefix.endswith("/8")
        byte = int(prefix.removesuffix("/8"))
        prefix = f"{byte}.0.0.0/8"
        assignments[prefix] = designation
    df = pd.read_csv(ipv6_filename)
    for row in df.itertuples():
        assignments[row.Prefix] = row.Designation
    return assignments


@memory.cache
def load_asn2info(filename) -> dict[int, tuple[str, str]]:
    asn2info = {}
    orgs = {}
    with fsspec.open(filename, compression="infer") as f:
        for line in f:
            row = json.loads(line)
            try:
                name = row["name"]
                organization_id = row["organizationId"]
                if row["type"] == "Organization":
                    orgs[organization_id] = name
                else:
                    asn = int(row["asn"])
                    asn2info[asn] = (name, orgs[organization_id])
            except KeyError:
                pass
    return asn2info


@memory.cache(ignore=["print_progress"])
def load_origins(
    collector: str, date: datetime, *, print_progress: bool = False
) -> dict[str, int]:
    collector = Collector.from_fqdn(collector)
    with TemporaryDirectory() as tmpdir:
        collector.download_rib(date, tmpdir, "rib")
        origins = mrtx.parse_mrt_file(
            os.path.join(tmpdir, "rib"), print_progress=print_progress
        )
        origins_single = {}
        for prefix, origin in origins.items():
            if isinstance(origin, set):
                origin = origin.pop()
            origins_single[prefix] = origin
        return origins_single
