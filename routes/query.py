# ==========================================
# 1. IMPORTS
# ==========================================
import os
from dotenv import load_dotenv
from fastapi import APIRouter

# LangChain and AI modules
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.messages import HumanMessage, SystemMessage

# (Your commented code for the native Hugging Face approach)
# from huggingface_hub import InferenceClient

# ==========================================
# 2. ENVIRONMENT SETUP
# ==========================================
# Load variables from the .env file
load_dotenv()

# Grab the token from the environment
hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# ==========================================
# 3. ROUTER SETUP
# ==========================================
router = APIRouter(
    prefix="/query",
    tags=["Query"]
)

# ==========================================
# 4. GLOBAL INITIALIZATION (Runs once on startup)
# ==========================================
# By putting these outside the @router.post function, they only load once 
# when your server starts, rather than restarting on every single user request.

# A. Initialize the Embedding Model (Converts text to vectors)
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# B. Initialize the Vector Database (Searches vectors)
vector_db = QdrantVectorStore.from_existing_collection(
    embedding=embedding_model,
    collection_name="sample_collection",
    url="http://localhost:6333"
)

# C. Initialize the Base LLM
hugging_face_client = HuggingFaceEndpoint(
    repo_id="basically-ai/Pebble-25M",
    huggingfacehub_api_token=hf_token, 
    max_new_tokens=512,
    temperature=0.3
)

# D. Wrap the LLM in ChatHuggingFace to support "conversational" task format
chat_model = ChatHuggingFace(llm=hugging_face_client)


# ==========================================
# 5. API ROUTE (Runs on every user request)
# ==========================================
@router.post("/")
async def query(question: str):
    
    # --- Step 1: Retrieval (RAG) ---
    search_results = vector_db.similarity_search(question)
    print(f"Search results for '{question}': {search_results}")

    # --- Step 2: Format the Context ---
    # Combine the retrieved documents into one string, including page numbers
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

    # Pass structured messages to avoid the "text-generation" error
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=question)
    ]

    # (Your old code: This single string prompt would cause an error with chat_model)
    # prompt = SYSTEM_PROMPT + f"\n\nQuestion: {question}\nAnswer:"

    # --- Step 4: Generate the Answer ---
    # FIXED: Pass 'messages' instead of 'prompt'
    response = chat_model.invoke(messages)
    
    # 'response' is an AIMessage object, so we extract the actual text using '.content'
    answer_text = response.content
    print(answer_text)

    # --- Step 5: Return to User ---
    return {
        "Question": question, 
        "Answer": answer_text, 
        "Context": context
    }


# ==========================================
# 6. YOUR COMMENTED ALTERNATIVE CODE
# ==========================================
# If you ever decide to drop LangChain's generator and use the native client:
# 
# # NOW your syntax works perfectly!
# # response = hugging_face_client.chat.completions.create(
# #     model="mistralai/Mistral-7B-Instruct-v0.2",
# #     messages=[
# #         {"role": "system", "content": "You are a helpful assistant."},
# #         {"role": "user", "content": question}
# #     ],
# #     max_tokens=512,
# #     temperature=0.3
# # )