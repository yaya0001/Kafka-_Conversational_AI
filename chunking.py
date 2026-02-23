from pypdf import PdfReader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma

embeddings = OllamaEmbeddings(model="nomic-embed-text")

vectordb = Chroma(
    embedding_function=embeddings,
    persist_directory="./kafka_db"
)
lc_semantic_chunker = SemanticChunker(
    embeddings=embeddings)

Work = ["the hunger artist", "A-country-doctor-by-Franz-Kafka", "AN_IMPERIAL_MESSAGE", 
     "Before the law", "in-the-penal-colony", 
     "Jackals and Arabs", "Metamorphosis","Franz Kafka-The Castle (Oxford World's Classics) (2009)", "The Trial - Franz Kafka"]
personal=['max interview','letters-to-felice','letters_to_milena','Kafka_life','Dearest Father','the-diaries_text','Kafkaesque']

import re


def clean_text(text):
    # Preserve paragraph breaks for semantic chunking
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Max 2 consecutive newlines
    text = re.sub(r' +', ' ', text)  # Collapse multiple spaces
    text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)  # Remove control chars
    return text.strip()

def add_to_db(docs, author, source, typ):
    # Safety splitter for oversized chunks
    safety_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " "]
    )
    
    for i in docs:
        reader = PdfReader(f"data for RAG/{i}.pdf")
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        cleaned = clean_text(text)
        
        # Semantic chunking
        semantic_chunks = lc_semantic_chunker.create_documents([cleaned])
        
        # CRITICAL: Split any chunks that are too large
        final_chunks = []
        for chunk in semantic_chunks:
            chunk_len = len(chunk.page_content)
            if chunk_len > 6000:  # Too large for embedding (leaves safety margin)
                print(f"  ⚠️ Splitting oversized chunk ({chunk_len} chars)")
                sub_chunks = safety_splitter.create_documents([chunk.page_content])
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)
        
        # Add metadata
        for j, doc in enumerate(final_chunks):
            doc.metadata = {
                "author": author,
                "source": source,
                "type": typ,
                "work": i,
                "chunk_id": j,
                "original_file": i + ".pdf",
                "chunk_chars": len(doc.page_content)
            }
        
        vectordb.add_documents(final_chunks)
        
        avg_size = sum(len(d.page_content) for d in final_chunks) / len(final_chunks)
        max_size = max(len(d.page_content) for d in final_chunks)
        print(f"✓ {i}: {len(final_chunks)} chunks | Avg: {avg_size:.0f} | Max: {max_size} chars")
    
    print(f"\n Total documents in DB: {vectordb._collection.count()}")

add_to_db(personal, "Kafka & others", "Letters", "personal")