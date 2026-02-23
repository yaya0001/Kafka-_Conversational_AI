from pypdf import PdfReader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma

embeddings = OllamaEmbeddings(model="nomic-embed-text")

def load_db():
    vectordb = Chroma(
        persist_directory=".\kafka_db",
        embedding_function=embeddings
    )
    print("DB is ready.")
    return vectordb
'''results = load_db()._collection.get(
    where={"work": "Dearest Father"},
    include=["metadatas", "documents"]
)

print("Number of chunks:", len(results["documents"]))

for i in range(len(results["documents"])):
    print("\nChunk", i+1)
    print("Metadata:", results["metadatas"][i])
    print("Preview:", results["documents"][i][:200])
'''





