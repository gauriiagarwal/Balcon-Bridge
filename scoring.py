"""Connectivity maths for Balcon Bridge. All scores are heuristic estimates."""

import math
from math import asin, cos, radians, sin, sqrt

import networkx as nx


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lng1, lat2, lng2 = map(radians, (a[0], a[1], b[0], b[1]))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return 2 * 6371000 * asin(sqrt(h))


def _pt(n: dict) -> tuple[float, float]:
    return n["lat"], n["lng"]


def match_plant(name: str, plants: dict) -> str | None:
    """Find our plant key from a typed/common/scientific name."""
    n = name.strip().lower()
    if not n:
        return None
    for genus, info in plants.items():
        if genus in n or any(c in n for c in info["common"]):
            return genus
    return None


def analyze(home: tuple[float, float], patches: list[dict], threshold_m: float) -> dict:
    """Build the patch network. Two places are 'connected' if within threshold_m."""
    nodes = {"home": {"lat": home[0], "lng": home[1], "name": "Your balcony", "kind": "home"}}
    for i, p in enumerate(patches):
        nodes[f"p{i}"] = p

    ids = list(nodes)
    G = nx.Graph()
    G.add_nodes_from(ids)
    edges = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            d = haversine_m(_pt(nodes[ids[i]]), _pt(nodes[ids[j]]))
            if d <= threshold_m:
                G.add_edge(ids[i], ids[j])
                edges.append((ids[i], ids[j]))

    comps = [set(c) for c in nx.connected_components(G)]
    home_idx = next(i for i, c in enumerate(comps) if "home" in c)

    # Candidate gaps between every pair of clusters (closest pair of places)
    cand = []
    for a in range(len(comps)):
        for b in range(a + 1, len(comps)):
            best = None
            for u in comps[a]:
                for v in comps[b]:
                    d = haversine_m(_pt(nodes[u]), _pt(nodes[v]))
                    if best is None or d < best[0]:
                        best = (d, u, v)
            cand.append((best[0], a, b, best[1], best[2]))
    cand.sort()

    # Kruskal: keep only the gaps that actually merge clusters (minimum bridges needed)
    parent = list(range(len(comps)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    gaps = []
    for d, a, b, u, v in cand:
        ra, rb = find(a), find(b)
        if ra == rb:
            continue
        parent[ra] = rb
        n_stones = max(1, math.ceil(d / threshold_m) - 1)
        pu, pv = _pt(nodes[u]), _pt(nodes[v])
        stones = [
            {
                "lat": pu[0] + (pv[0] - pu[0]) * i / (n_stones + 1),
                "lng": pu[1] + (pv[1] - pu[1]) * i / (n_stones + 1),
            }
            for i in range(1, n_stones + 1)
        ]
        gaps.append({"ci": a, "cj": b, "a": u, "b": v, "dist": d, "stones": stones})

    return {"nodes": nodes, "edges": edges, "comps": comps, "home_idx": home_idx, "gaps": gaps}


def apply_bridges(an: dict, k: int) -> tuple[int, list[dict]]:
    """If the k smallest gaps are bridged: (patches connected to you, stepping-stone points)."""
    parent = list(range(len(an["comps"])))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for g in an["gaps"][:k]:
        parent[find(g["ci"])] = find(g["cj"])

    root = find(an["home_idx"])
    members = set()
    for idx, c in enumerate(an["comps"]):
        if find(idx) == root:
            members |= c
    members.discard("home")
    stones = [s for g in an["gaps"][:k] for s in g["stones"]]
    return len(members), stones


def score(owned: list[str], plants: dict, patches_connected: int) -> tuple[float, float, float]:
    """(total, plant_part, connectivity_part), each out of 5 / 10. Heuristic estimate."""
    quality = sum(plants.get(g, {}).get("value", 1) for g in set(owned))
    plant_part = min(5.0, quality * 0.7)
    conn_part = min(5.0, patches_connected * 1.25)
    return round(plant_part + conn_part, 1), round(plant_part, 1), round(conn_part, 1)


def missing_seasons(owned: list[str], plants: dict) -> list[str]:
    have = set()
    for g in set(owned):
        have |= set(plants.get(g, {}).get("bloom", []))
    return [s for s in ("summer", "monsoon", "winter") if s not in have]


def recommend(owned: list[str], plants: dict) -> list[tuple[str, dict]]:
    """Plants to add so every season has something in bloom."""
    owned_set = set(owned)
    recs = []
    for season in missing_seasons(owned, plants):
        options = [
            (g, i)
            for g, i in plants.items()
            if g not in owned_set and season in i["bloom"] and "note" not in i
        ]
        options.sort(key=lambda x: -x[1]["value"])
        for g, i in options[:2]:
            if g not in [r[0] for r in recs]:
                recs.append((g, {**i, "for_season": season}))
    return recs


def upgrade_plants(owned: list[str], plants: dict) -> tuple[list[str], list[str], list[str]]:
    """Swap weak plants (value 1 or unknown) for better ones and fill empty bloom seasons.
    Returns (upgraded_plant_list, dropped, added)."""
    uniq = sorted(set(owned))
    keep = [g for g in uniq if plants.get(g, {}).get("value", 1) >= 2]
    dropped = [g for g in uniq if g not in keep]
    added = [g for g, _ in recommend(keep, plants)]
    if len(added) < len(dropped):
        extra = sorted(
            (g for g, i in plants.items() if g not in keep and g not in added and "note" not in i),
            key=lambda g: -plants[g]["value"],
        )
        added += extra[: len(dropped) - len(added)]
    return keep + added, dropped, added
