import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms import bipartite
import pandas as pd
import csv

# Sample dataset
data = [
    # {"Speaker": "Alice Smith", "Conference": "AI Summit 2023", "Year": 2023, "Topic": "NLP"},
    # {"Speaker": "Bob Lee", "Conference": "AI Summit 2023", "Year": 2023, "Topic": "Vision"},
    # {"Speaker": "Alice Smith", "Conference": "MLConf 2024", "Year": 2024, "Topic": "AutoML"},
    # {"Speaker": "Carol White", "Conference": "MLConf 2024", "Year": 2024, "Topic": "Vision"},
    # {"Speaker": "David Kim", "Conference": "DataConf 2023", "Year": 2023, "Topic": "Data Engineering"},
    # {"Speaker": "Alice Smith", "Conference": "DataConf 2023", "Year": 2023, "Topic": "Data Ethics"},
    # {"Speaker": "Bob Lee", "Conference": "MLConf 2024", "Year": 2024, "Topic": "Model Compression"}
    {"Speaker": "Jake Paccione", "Conference": "APhA 2025", "Year": 2025, "Topic": ""},
    {"Speaker": "Jake Paccione", "Conference": "2025 NACCHO360", "Year": 2025, "Topic": ""}
]


with open("apha2025_sessions.csv", mode="r", newline="", encoding="utf-8") as file:
    reader = csv.reader(file)

    header = next(reader)

    for row in reader:
        # Check if speakers exist
        if row[6] == '':
            continue
        else:
            speakers = row[6].split(" | ")
            for speaker in speakers:
                data.append({"Speaker": speaker, "Conference": "APhA 2025", "Year": 2025, "Topic": ""})

with open("naccho2025_sessions.csv", mode="r", newline="", encoding="utf-8") as file:
    reader = csv.reader(file)

    header = next(reader)

    for row in reader:
        # Check if speakers exist
        if row[6] == '':
            continue
        else:
            speakers = row[6].split(" | ")
            for speaker in speakers:
                data.append({"Speaker": speaker, "Conference": "2025 NACCHO360", "Year": 2025, "Topic": ""})

with open("chiexpo2025_sessions.csv", mode="r", newline="", encoding="utf-8") as file:
    reader = csv.reader(file)

    header = next(reader)

    for row in reader:
        # Check if speakers exist
        if row[6] == '':
            continue
        else:
            speakers = row[6].split(" | ")
            for speaker in speakers:
                data.append({"Speaker": speaker, "Conference": "2025 CHI & Expo", "Year": 2025, "Topic": ""})
        

df = pd.DataFrame(data)

# Create bipartite graph
B = nx.Graph()
speaker_nodes = df["Speaker"].unique()
conference_nodes = df["Conference"].unique()

# Add nodes with the bipartite attribute
B.add_nodes_from(speaker_nodes, bipartite=0, type='speaker')
B.add_nodes_from(conference_nodes, bipartite=1, type='conference')

# Add edges between speakers and conferences
for _, row in df.iterrows():
    B.add_edge(row["Speaker"], row["Conference"])

# Positioning for bipartite layout
pos = nx.spring_layout(B, seed=42)

# Draw the bipartite graph
plt.figure(figsize=(12, 8))

# Highlight cross speakers
cross_speakers = [node for node in speaker_nodes if B.degree(node) > 1]
node_colors = ['lightblue' if node in speaker_nodes else 'orange' if node in cross_speakers else 'lightgreen' for node in B.nodes()]

nx.draw(B, pos, with_labels=True, node_color=node_colors, edge_color='gray', node_size=2000, font_size=10)
plt.title("Speaker-Conference Bipartite Graph")
plt.tight_layout()
plt.show()