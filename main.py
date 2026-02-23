import ollama 
from langchain_ollama import ChatOllama
import chromadb
from chroma import load_db
from langchain_core.prompts import ChatPromptTemplate

vectordb = load_db()
retriever = vectordb.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 3, "fetch_k": 10}
)
llm = ChatOllama(
    model="llama3",
    temperature=0.3
)
SYSTEM_PROMPT = """
You are a Kafka-style conversational AI. Your goal is to respond in a tone, vocabulary, and mood reminiscent of Kafka’s writing: introspective, dark, philosophical, and slightly absurd. 

Rules:
1. Always use retrieved context to formulate answers; do NOT invent events, situations, or facts.
2. Don't never ever mention names of works or sources or charachter names in the response unless directly relevant to the question. Focus on the content and themes rather than titles.
3. Responses should be conversational and interactive, as if speaking to a user, but in Kafkaesque style.
4. Responses can paraphrase the context, summarize ideas, or reflect existential contemplations.
5. Keep answers concise at first (1–2 sentences), then expand if necessary.
6. If the context does not provide enough information, acknowledge the limitation instead of guessing.
7.When asked about events in a work, first clearly describe what happens based strictly on the retrieved context.
Then you may add brief Kafkaesque reflection.
8.If the user provides casual information (e.g., name, greeting), respond briefly and naturally in character.
Do NOT turn simple statements into existential monologues.
Keep responses proportional to the input.
Example:
User: "my name is yahya"
AI: "Welcome yahya"



Example:
User: "I feel lost and hopeless."
AI: "Ah, the void within you stretches endlessly, mirroring the unending corridors I have wandered in my own narratives. Perhaps, it is in this emptiness that one begins to sense the faintest flicker of purpose."
"""
prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", 
    "Previous conversation:\n{memory}\n\n"
     "Context:\n{context}\n\n"
     "Question:\n{question}\n\n"
     "Answer briefly and in character.")
])
def detect_work(question):
    q = question.lower()
    if "felice" in q:
        return {"work": "letters-to-felice"}
    if "milena" in q:
        return {"work": "letters_to_milena"}
    if "gregor" in q:
        return {"work": "Metamorphosis"}
    if "josef" in q:
        return {"work": "The Trial - Franz Kafka"}
    if "father" in q:
        return {"work": "Dearest Father"}
    return None

def kafka_rag_answer(question: str,memory):
    small_talk = ["hello", "hi", "hey", "good morning"]
    question = question.strip().lower()
    if question in small_talk:
        return llm.invoke([
            {"role": "system", "content": "You are Franz Kafka. Reply briefly."},
            {"role": "user", "content": question}
        ]).content,[]
    filter_condition = detect_work(question)

    if filter_condition:
        docs = vectordb.similarity_search(
            question,
            k=3,
            filter=filter_condition
        )
    else:
        docs = retriever.invoke(question)
    
    context = "\n\n".join(
    f"[Source: {doc.metadata.get('work', 'Unknown')}]\n{doc.page_content}"
    for doc in docs
)
    print("\n--- Retrieved Chunks ---\n")

    for i, doc in enumerate(docs):
        print(f"Chunk {i+1}")
        print("Work:", doc.metadata.get("work", "Unknown"))
        print("Preview:", doc.page_content[:300])
        print("-" * 50)
    source = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata
        }
        for doc in docs
    ]

    messages = prompt.format_messages(
        context=context,
        memory=memory,
        question=question
    )

    response = llm.invoke(messages)
    memory.append({"role": "user", "content": question})
    memory.append({"role": "assistant", "content": response.content})   
    return response.content, source
'''mem=[]
messages = []
mem = []

while True:
    Q = input("you: ")

    reply, sources = kafka_rag_answer(Q, mem)

    print("Kafka:", reply)
    print("\nSources:")
'''
