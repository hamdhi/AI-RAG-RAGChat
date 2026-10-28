from dotenv import load_dotenv

from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import QdrantVectorStore
import os

# Load Environment Variables
load_dotenv()

# Define the path to the PDF file / also can use function or a api call to get the file path
pdf_path = Path(__file__).parent / "data" / "sample.pdf"

# Load The Pdf File into memory using langchain
loader = PyPDFLoader(str(pdf_path))
docs = loader.load()

# Split the document into chunks
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=0
)

chunks = text_splitter.split_documents(docs)

# Embedding the chunks using OpenAI Embeddings
# embedding_model = OpenAIEmbeddings(
#     model="text-embedding-3-large",
#     api_key=os.getenv("OPEN_API_KEY")
# )

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# Create a Qdrant Vector Store
vector_store = QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embedding_model,
    collection_name="sample_collection",
    url="http://localhost:6333"
)

print("Vector store created and documents embedded successfully.")