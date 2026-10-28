# ==========================================
# 1. IMPORTS
# ==========================================
import os
from dotenv import load_dotenv
from fastapi import APIRouter

# LangChain - Groq for the LLM
from langchain_groq import ChatGroq

# LangChain - Hugging Face for Embeddings & Qdrant for Vector DB
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.messages import HumanMessage, SystemMessage

# ==========================================
# 2. ENVIRONMENT SETUP
# ==========================================
load_dotenv()

# Verify the Groq API key is loaded
if not os.getenv("GROQ_API_KEY"):
    print("WARNING: GROQ_API_KEY not found in .env file!")

router = APIRouter(
    prefix="/query",
    tags=["Query"]
)

# ==========================================
# 3. GLOBAL INITIALIZATION (Runs once on startup)
# ==========================================

# A. Initialize the Embedding Model (Runs locally, tiny ~90MB)
print("Loading Hugging Face Embeddings...")
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# B. Initialize the Vector Database (Qdrant)
print("Connecting to Qdrant...")
vector_db = QdrantVectorStore.from_existing_collection(
    embedding=embedding_model,
    collection_name="sample_collection",
    url="http://localhost:6333"
)

# C. Initialize Groq Cloud LLM (Blazing fast, stable free tier)
print("Initializing Groq LLM...")
chat_model = ChatGroq(
    model="openai/gpt-oss-20b", # Reliable, fast Llama 3 model
    temperature=0.3,
    max_tokens=512,
    # The API key is automatically pulled from the GROQ_API_KEY environment variable
)


# ==========================================
# 4. API ROUTE
# ==========================================
@router.post("/")
async def query(question: str):
    
    # --- Step 1: Retrieval (RAG) ---
    search_results = vector_db.similarity_search(question)
    
    # --- Step 2: Format the Context ---
    context = " ".join([
        f"Page {doc.metadata.get('page', 'Unknown')}: {doc.page_content}" 
        for doc in search_results
    ])

    # --- Step 3: Build the Prompt ---
    SYSTEM_PROMPT = f"""
    You are a helpful assistant that provides answers based on the provided context.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    
    Context:
    {context}
    """

    # Format as structured messages
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=question)
    ]

    # --- Step 4: Generate the Answer ---
    # This sends the request to Groq and returns almost instantly
    response = chat_model.invoke(messages)
    
    # Extract the text from the AIMessage object
    answer_text = response.content
    print(f"Generated Answer: {answer_text}")

    # --- Step 5: Return to User ---
    return {
        "Question": question, 
        "Answer": answer_text, 
        "Context": context
    }