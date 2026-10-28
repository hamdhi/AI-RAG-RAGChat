# ==========================================
# 1. IMPORTS
# ==========================================
import os
from dotenv import load_dotenv
from fastapi import APIRouter

# LangChain modules for Cloud API and RAG
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.messages import HumanMessage, SystemMessage

# ==========================================
# 2. ENVIRONMENT SETUP
# ==========================================
load_dotenv()

# Grab the token from the environment
hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

router = APIRouter(
    prefix="/query",
    tags=["Query"]
)

# ==========================================
# 3. GLOBAL INITIALIZATION (Runs once on startup)
# ==========================================

# A. Initialize the Embedding Model (Tiny ~90MB download, runs locally)
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# B. Initialize the Vector Database
vector_db = QdrantVectorStore.from_existing_collection(
    embedding=embedding_model,
    collection_name="sample_collection",
    url="http://localhost:6333"
)

# C. Initialize the Cloud LLM (No local download, runs on Hugging Face servers)
hugging_face_client = HuggingFaceEndpoint(
    repo_id="microsoft/Phi-3-mini-4k-instruct", # Reliable free tier model
    huggingfacehub_api_token=hf_token, 
    max_new_tokens=512,
    temperature=0.3
)

# D. Wrap the LLM to support chat messages
chat_model = ChatHuggingFace(llm=hugging_face_client)


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

    # Format as structured messages for the API
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=question)
    ]

    # --- Step 4: Generate the Answer ---
    # This sends the request to Hugging Face and waits for the response
    response = chat_model.invoke(messages)
    
    # Extract the text from the AIMessage object
    answer_text = response.content
    print(answer_text)

    # --- Step 5: Return to User ---
    return {
        "Question": question, 
        "Answer": answer_text, 
        "Context": context
    }