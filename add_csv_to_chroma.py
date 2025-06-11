import csv
import chromadb
from sentence_transformers import SentenceTransformer
import re

client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="session_info")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def populate_from_csv(path):
    """Scrapes CSV and adds data to ChromaDB if the collection is empty."""
    if collection.count() == 0:
        with open(path, mode="r", newline="", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                for i, row in enumerate(reader):
                    full_chunks=[]
                    desc_count=1
                    for j in range(0, len(row["Description"]), 500):
                        chunk=f"""
                        Title: {row["Title"]}
                        Date: {row["Date"]}
                        Start Time: {row["Start Time"]} 
                        End Time: {row["End Time"]}
                        Location: {row["Location"]}
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
                    if i % 100 == 0:
                        print(f"Processed session {i}")
                print("Database population from csv complete.")
    else:
        print("Database already contains data from URLs. Skipping URL population.")
   
def prompt_database(query):
    """Prompts the Chroma database by performing a simple similarity search."""
    query = query
    query_embedding = embedder.encode([query])[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=15)
    results_list = []
    if results and results['documents'] and results['distances']:
        for i, doc in enumerate(results['documents'][0]):
            results_list.append({
                "text": doc,
                "score": results['distances'][0][i]
            })
    else:
        results_list.append("No results found in the database.")

    return results_list




if __name__ == "__main__":
    populate_from_csv("apha2025_sessions.csv")
    query = input("Prompt: ")
    data = prompt_database(query)
