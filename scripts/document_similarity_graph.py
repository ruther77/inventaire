"""
Analyse de similarité textuelle et clustering par graphe sur un fichier Markdown.

Usage (exemple) :
    python scripts/document_similarity_graph.py docs/DOCUMENTATION_PROJET.md \
        --model sentence-transformers/all-MiniLM-L12-v2 \
        --min-sim 0.55 \
        --top-k 15

Fonctionnement :
- Découpe le document en chunks (titres + paragraphes) avec chevauchement léger.
- Encode chaque chunk en embedding dense (SentenceTransformers).
- Construit un graphe pondéré (cosinus) k-NN filtré par seuil.
- Applique Leiden (si igraph+leidenalg dispo), sinon Louvain, sinon Chinese Whispers interne.
- Génère des labels par cluster via TF-IDF local (mots-clés top-N).
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Callable, Iterable, List, Tuple

import numpy as np


def _lazy_import_sentence_transformers():
    from sentence_transformers import SentenceTransformer  # type: ignore

    return SentenceTransformer


def _lazy_import_tfidf():
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore

    return TfidfVectorizer


def _lazy_import_faiss():
    try:
        import faiss  # type: ignore
    except Exception:
        return None
    return faiss


def _read_markdown(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _normalize_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _split_paragraphs(md: str) -> list[str]:
    # Conserve les titres pour le contexte, découpe sur doubles sauts de ligne.
    parts = re.split(r"\n{2,}", md)
    cleaned = [_normalize_text(p) for p in parts if _normalize_text(p)]
    return cleaned


def _chunk_with_overlap(paragraphs: list[str], target_tokens: int = 220, overlap: int = 40) -> list[Tuple[str, str]]:
    """
    Crée des chunks avec titres contextuels.
    Retourne une liste de (chunk_id, texte).
    """
    chunks: list[Tuple[str, str]] = []
    buffer: list[str] = []
    token_count = 0
    chunk_idx = 0

    def flush():
        nonlocal buffer, token_count, chunk_idx
        if not buffer:
            return
        text = " ".join(buffer).strip()
        if text:
            chunks.append((f"chunk_{chunk_idx:04d}", text))
            chunk_idx += 1
        # Recule pour l'overlap
        if overlap > 0:
            tokens = " ".join(buffer).split()
            buffer = tokens[-overlap:]
            token_count = len(buffer)
        else:
            buffer = []
            token_count = 0

    for para in paragraphs:
        words = para.split()
        if not words:
            continue
        if words[0].startswith("#"):
            # Titre : on force un flush pour conserver les sections.
            flush()
        buffer.extend(words)
        token_count += len(words)
        if token_count >= target_tokens:
            flush()
    flush()
    return chunks


def _embed_chunks(chunks: list[str], model_name: str, device: str | None = None) -> np.ndarray:
    """
    Encode les chunks avec SentenceTransformers; si le modèle n'est pas accessible
    (mode offline / pas de réseau), bascule en fallback TF-IDF L2-normalisé.
    """

    try:
        SentenceTransformer = _lazy_import_sentence_transformers()
        model_kwargs = {"device": device} if device else {}
        model = SentenceTransformer(model_name, **model_kwargs)
        embeddings = model.encode(chunks, batch_size=32, normalize_embeddings=True, show_progress_bar=True)
        return np.asarray(embeddings, dtype=np.float32)
    except Exception as exc:
        print(f"[warn] Impossible de charger le modèle '{model_name}' ({exc}); fallback TF-IDF local.")
        return _embed_chunks_tfidf(chunks)


def _embed_chunks_tfidf(chunks: list[str]) -> np.ndarray:
    """Fallback offline : TF-IDF (1-2 grams) L2-normalisé, converti en float32 dense."""

    TfidfVectorizer = _lazy_import_tfidf()
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=20000)
    mat = vectorizer.fit_transform(chunks)
    # L2-normalisation implicite via tf-idf; convertissons en dense pour le kNN cosinus.
    dense = mat.astype(np.float32).toarray()
    # Normalisation supplémentaire pour être robuste
    norms = np.linalg.norm(dense, axis=1, keepdims=True) + 1e-8
    dense = dense / norms
    return dense


def _topk_cosine_faiss(emb: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
    faiss = _lazy_import_faiss()
    if faiss is None:
        raise RuntimeError("faiss non disponible")
    d = emb.shape[1]
    index = faiss.IndexFlatIP(d)
    index.add(emb)
    sims, idxs = index.search(emb, k)
    return idxs, sims


def _topk_cosine_numpy(emb: np.ndarray, k: int) -> Tuple[np.ndarray, np.ndarray]:
    # Cosinus déjà normalisés => dot product
    sims = emb @ emb.T
    np.fill_diagonal(sims, -np.inf)
    idxs = np.argpartition(-sims, kth=range(k), axis=1)[:, :k]
    top_sims = np.take_along_axis(sims, idxs, axis=1)
    return idxs, top_sims


def _build_graph(
    emb: np.ndarray,
    ids: list[str],
    top_k: int = 15,
    min_sim: float = 0.55,
) -> dict[str, list[Tuple[str, float]]]:
    use_faiss = _lazy_import_faiss() is not None
    idxs, sims = (_topk_cosine_faiss(emb, top_k + 1) if use_faiss else _topk_cosine_numpy(emb, top_k + 1))
    graph: dict[str, list[Tuple[str, float]]] = defaultdict(list)
    n = len(ids)
    for i in range(n):
        src = ids[i]
        for j in range(idxs.shape[1]):
            tgt_idx = idxs[i, j]
            sim = sims[i, j]
            if tgt_idx < 0 or tgt_idx >= n:
                continue
            if sim < min_sim:
                continue
            tgt = ids[tgt_idx]
            if src == tgt:
                continue
            graph[src].append((tgt, float(sim)))
    return graph


def _cluster_leiden(graph_edges: list[Tuple[int, int, float]], n_nodes: int) -> list[int]:
    import igraph as ig  # type: ignore
    import leidenalg as la  # type: ignore

    g = ig.Graph()
    g.add_vertices(n_nodes)
    g.add_edges([(u, v) for u, v, _ in graph_edges])
    g.es["weight"] = [w for _, _, w in graph_edges]
    part = la.find_partition(g, la.RBConfigurationVertexPartition, weights="weight", resolution_parameter=1.0)
    return part.membership


def _cluster_louvain(graph_edges: list[Tuple[int, int, float]], n_nodes: int) -> list[int]:
    import networkx as nx  # type: ignore
    import community  # type: ignore

    g = nx.Graph()
    for u, v, w in graph_edges:
        g.add_edge(u, v, weight=w)
    mapping = community.best_partition(g, weight="weight")
    labels = [0] * n_nodes
    for node, cid in mapping.items():
        labels[node] = cid
    return labels


def _cluster_chinese_whispers(graph_edges: list[Tuple[int, int, float]], n_nodes: int, iterations: int = 20) -> list[int]:
    # Implémentation minimaliste.
    labels = list(range(n_nodes))
    adjacency: dict[int, list[Tuple[int, float]]] = defaultdict(list)
    for u, v, w in graph_edges:
        adjacency[u].append((v, w))
        adjacency[v].append((u, w))
    for _ in range(iterations):
        nodes = list(range(n_nodes))
        np.random.shuffle(nodes)
        for node in nodes:
            votes = defaultdict(float)
            for neighbor, weight in adjacency.get(node, []):
                votes[labels[neighbor]] += weight
            if votes:
                labels[node] = max(votes.items(), key=lambda x: x[1])[0]
    return labels


def _cluster(graph: dict[str, list[Tuple[str, float]]], ids: list[str]) -> list[int]:
    id_to_idx = {id_: i for i, id_ in enumerate(ids)}
    edges: list[Tuple[int, int, float]] = []
    for src, targets in graph.items():
        for tgt, w in targets:
            edges.append((id_to_idx[src], id_to_idx[tgt], w))

    try:
        return _cluster_leiden(edges, len(ids))
    except Exception:
        try:
            return _cluster_louvain(edges, len(ids))
        except Exception:
            return _cluster_chinese_whispers(edges, len(ids))


def _label_clusters(chunks: list[str], memberships: list[int], top_terms: int = 6) -> dict[int, list[str]]:
    TfidfVectorizer = _lazy_import_tfidf()
    labels: dict[int, list[str]] = {}
    by_cluster: defaultdict[int, list[str]] = defaultdict(list)
    for text, cid in zip(chunks, memberships):
        by_cluster[cid].append(text)
    for cid, texts in by_cluster.items():
        vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1, 2), stop_words="english")
        try:
            tfidf = vectorizer.fit_transform(texts)
        except ValueError:
            labels[cid] = []
            continue
        scores = np.asarray(tfidf.sum(axis=0)).ravel()
        terms = np.array(vectorizer.get_feature_names_out())
        top_idx = np.argsort(-scores)[:top_terms]
        labels[cid] = [terms[i] for i in top_idx]
    return labels


@dataclass
class Chunk:
    id: str
    text: str
    cluster: int | None = None


def _maybe_save_graph(
    graph: dict[str, list[Tuple[str, float]]],
    ids: list[str],
    memberships: list[int],
    out_path: str | None,
    max_nodes: int,
) -> None:
    """Optionnel : enregistre un PNG du graphe (spring layout, cluster color)."""

    if not out_path:
        return
    try:
        import networkx as nx  # type: ignore
        import matplotlib.pyplot as plt  # type: ignore
    except Exception as exc:
        print(f"[warn] Graph non enregistré (matplotlib/networkx indisponible : {exc})")
        return

    g = nx.Graph()
    for src, targets in graph.items():
        for tgt, w in targets:
            g.add_edge(src, tgt, weight=w)

    # Limiter le graphe si trop dense
    if g.number_of_nodes() > max_nodes:
        # Garder les nœuds avec plus haut degré
        degrees = sorted(g.degree, key=lambda kv: kv[1], reverse=True)
        keep = {node for node, _ in degrees[:max_nodes]}
        g = g.subgraph(keep).copy()

    # Relayout
    pos = nx.spring_layout(g, weight="weight", seed=42, k=None, iterations=100)

    # Couleurs par cluster
    cid_by_node = {id_: memberships[ids.index(id_)] if id_ in ids else -1 for id_ in g.nodes()}
    clusters = sorted(set(cid_by_node.values()))
    cmap = plt.cm.get_cmap("tab20", len(clusters))
    node_colors = [cmap(clusters.index(cid_by_node[n]) % cmap.N) for n in g.nodes()]
    node_sizes = [60 + 120 * math.log1p(g.degree(n)) for n in g.nodes()]

    plt.figure(figsize=(10, 8))
    nx.draw_networkx_edges(g, pos, alpha=0.2, width=[g[u][v].get("weight", 0.5) * 1.5 for u, v in g.edges()])
    nx.draw_networkx_nodes(g, pos, node_color=node_colors, node_size=node_sizes, linewidths=0.2, edgecolors="k", alpha=0.9)
    plt.axis("off")
    plt.title("Graphe de similarité (clusters colorés)", fontsize=12)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"[info] Graphe sauvegardé : {out_path}")


def run(args: argparse.Namespace) -> None:
    raw = _read_markdown(args.path)
    paragraphs = _split_paragraphs(raw)
    chunk_pairs = _chunk_with_overlap(paragraphs, target_tokens=args.chunk_tokens, overlap=args.overlap)
    if not chunk_pairs:
        print("Aucun chunk généré", file=sys.stderr)
        return
    chunk_ids = [cid for cid, _ in chunk_pairs]
    chunk_texts = [txt for _, txt in chunk_pairs]

    print(f"[info] Chunks: {len(chunk_ids)} | model: {args.model}")
    emb = _embed_chunks(chunk_texts, args.model, device=args.device)

    graph = _build_graph(emb, chunk_ids, top_k=args.top_k, min_sim=args.min_sim)
    memberships = _cluster(graph, chunk_ids)
    labels = _label_clusters(chunk_texts, memberships, top_terms=args.label_terms)

    _maybe_save_graph(
        graph=graph,
        ids=chunk_ids,
        memberships=memberships,
        out_path=args.graph_png,
        max_nodes=args.graph_max_nodes,
    )

    clusters: defaultdict[int, list[int]] = defaultdict(list)
    for idx, cid in enumerate(memberships):
        clusters[cid].append(idx)

    print(f"[info] Clusters trouvés: {len(clusters)}")
    for cid, idxs in sorted(clusters.items(), key=lambda kv: -len(kv[1])):
        preview = "; ".join(labels.get(cid, [])[:args.label_terms]) or "(pas de label)"
        print(f"\n=== Cluster {cid} | {len(idxs)} chunks | labels: {preview}")
        for idx in idxs[: args.max_samples_per_cluster]:
            print(f"- {chunk_ids[idx]}: {chunk_texts[idx][:140]}{'...' if len(chunk_texts[idx])>140 else ''}")
        if len(idxs) > args.max_samples_per_cluster:
            print(f"  (+{len(idxs) - args.max_samples_per_cluster} autres)")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clustering par similarité textuelle d'un document Markdown.")
    parser.add_argument("path", help="Chemin du fichier Markdown (ex: docs/DOCUMENTATION_PROJET.md)")
    parser.add_argument("--model", default="sentence-transformers/all-MiniLM-L12-v2", help="Modèle SentenceTransformers")
    parser.add_argument("--device", default=None, help="Device pour le modèle (ex: cpu, cuda, mps)")
    parser.add_argument("--chunk-tokens", type=int, default=220, help="Taille cible des chunks (en tokens approx.)")
    parser.add_argument("--overlap", type=int, default=40, help="Chevauchement entre chunks")
    parser.add_argument("--top-k", type=int, default=15, help="Voisins k-NN pour le graphe")
    parser.add_argument("--min-sim", type=float, default=0.55, help="Seuil de similarité cosinus pour garder une arête")
    parser.add_argument("--label-terms", type=int, default=6, help="Nombre de mots-clés pour nommer un cluster")
    parser.add_argument(
        "--max-samples-per-cluster",
        type=int,
        default=8,
        help="Nombre d'exemples affichés par cluster (pour l'aperçu CLI)",
    )
    parser.add_argument("--graph-png", default=None, help="Chemin de sortie pour un PNG du graphe (optionnel)")
    parser.add_argument(
        "--graph-max-nodes",
        type=int,
        default=120,
        help="Nombre max de nœuds affichés sur le graphe (les plus connectés)",
    )
    return parser


if __name__ == "__main__":
    parser = build_arg_parser()
    args = parser.parse_args()
    if not os.path.exists(args.path):
        print(f"Fichier introuvable: {args.path}", file=sys.stderr)
        sys.exit(1)
    run(args)
