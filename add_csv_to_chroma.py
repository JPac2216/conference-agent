import csv
import chromadb
from sentence_transformers import SentenceTransformer

client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="session_info", metadata={"hnsw:space": "cosine"})
embedder = SentenceTransformer("all-MiniLM-L6-v2")

conference_list = ["APhA 2025", "NACCHO360 2025", "CHI Community Health Conference & Expo 2025"]

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
                        ids=[f"session_{i}_{j}" for j in range(len(full_chunks))],
                        metadatas=[{"conference": conference} for _ in full_chunks]
                    )
                if i % 100 == 0 and i > 0:
                    print(f"Processed session {i}")
            print(f"Database population from {path} complete.")

def retriever_tool(query: str) -> str:
    """This tool searches the Chroma database containing all of the session info and returns the top 10 chunks."""

    conference_filter = []
    for conference in conference_list:
        if conference.lower() in query.lower():
            conference_filter.append(conference)
            print(f"Added {conference} to the filter!")

    clean_query = query.lower()
    for conf in conference_list:
        clean_query = clean_query.replace(conf.lower(), "")
        clean_query = clean_query.replace(conf.split()[0].lower(), "")

    clean_query = clean_query.strip()
    print(clean_query)
    query_embedding = embedder.encode([clean_query])[0]

    args = {
        "query_embeddings": [query_embedding],
        "n_results": 10
    }

    if conference_filter:
        args["where"] = {"conference": {"$in": conference_filter}}

    query_results = collection.query(**args)
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
    #populate_from_csv("apha2025_sessions.csv", "APhA 2025")
    #populate_from_csv("naccho2025_sessions.csv", "NACCHO360 2025")
    #populate_from_csv("chiexpo2025_sessions.csv", "CHI Community Health Conference & Expo 2025")
    query = input("Prompt: ")
    data = retriever_tool(query)
    
