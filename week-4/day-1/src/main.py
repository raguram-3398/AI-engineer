from documents import load_sample_docs
from embeddings import Embedder
from faiss_index import Metric, build_faiss_index, search_index
from numpy_search import cosine_search

def print_results(title: str, results: list[tuple[int, float]], docs: list[str]) -> None:
    """Print ranked search results with their document text."""
    print(f"\n{title}")
    for rank, (doc_index, score) in enumerate(results, start=1):
        print(f"{rank}. score={score:.4f}\n" f"   {docs[doc_index]}")


def main() -> None:
    """Run the semantic search comparison using FAISS and NumPy."""
    docs = load_sample_docs()
    embedder = Embedder()
    document_embeddings = embedder.embed(docs)
    l2_index = build_faiss_index(document_embeddings, Metric.L2)
    ip_index = build_faiss_index(document_embeddings, Metric.INNER_PRODUCT)
    queries = ["cost of ownership", "keeping the application available during heavy demand", "protecting customer data",]
    for query in queries:
        query_embedding = embedder.embed([query])
        l2_results = search_index(l2_index, query_embedding, k=3)
        ip_results = search_index(ip_index, query_embedding, k=3)
        numpy_results = cosine_search(document_embeddings, query_embedding, k=3)
        print(f"\n{'=' * 60}")
        print(f"QUERY: {query}")
        print("=" * 60)
        print_results("FAISS — L2 (lower is better)", l2_results, docs)
        print_results("FAISS — Inner Product / Cosine (higher is better)", ip_results, docs)
        print_results("NumPy — Cosine Similarity (higher is better)", numpy_results, docs)

if __name__ == "__main__":
    main()