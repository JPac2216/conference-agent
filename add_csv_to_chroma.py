import csv
import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="session_info", metadata={"hnsw:space": "cosine"})
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def populate_from_csv(path: str, conference: str):
    """Scrapes CSV and adds data to ChromaDB."""
    with open(path, mode="r", newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for i, row in enumerate(reader):
                full_chunks=[]
                desc_count=1
                for j in range(0, len(row["Description"]), 500):
                    chunk=f"""
Conference: {conference}
Title: {row["Title"]}
Date: {row["Date"]}
Start Time: {row["Start Time"]} 
End Time: {row["End Time"]}
Location: {row["Location"]}
Preregistration: {row["Preregistration"]}
Presenters: {row["Presenters"]}
Professional Titles: {row["Professional Titles"]}
Institutions: {row["Institutions"]}
Sponsors: {row["Sponsors"]}
Description Chunk {desc_count}: {row["Description"][j:j+500]}"""
                    full_chunks.append(chunk)
                    desc_count+=1

                if full_chunks:
                    embeddings = embedder.encode(full_chunks)
                    collection.add(
                        documents=full_chunks,
                        embeddings=embeddings,
                        ids=[f"session_{i}_{j}" for j in range(len(full_chunks))]
                    )
                if i % 100 == 0 and i > 0:
                    print(f"Processed session {i}")
            print(f"Database population from {path} complete.")

def retriever_tool(query: str) -> str:
    """This tool searches the Chroma database containing all of the session info and returns the top 10 chunks."""
    query_embedding = embedder.encode([query])[0]
    query_results = collection.query(query_embeddings=[query_embedding], n_results=10)
    result = ""
    if query_results and query_results['documents'] and query_results['distances']:
        for i, doc in enumerate(query_results['documents'][0]):
            result += f"""
TEXT: {doc}
SCORE: {query_results['distances'][0][i]}
            """
        print(result)
    else:
        return "No results found in the database."


if __name__ == "__main__":
    populate_from_csv("apha2025_sessions.csv", "APHA 2025")
    # populate_from_csv("naccho2025_sessions.csv", "NACCHO360 2025")
    query = input("Prompt: ")
    data = retriever_tool(query)
