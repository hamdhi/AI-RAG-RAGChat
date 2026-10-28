from dotenv import load_dotenv
from fastapi import FastAPI
from routes.query import router as query_router
from routes.wokingquery import router as working_query_router
from routes.grok import router as grok_router

load_dotenv()

app = FastAPI(
    title="My FastRAGAPI Application",
    description="This is a simple FastAPI application with RAG capabilities.",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(query_router, prefix="/query", tags=["Query"])
app.include_router(working_query_router, prefix="/workingquery", tags=["Working Query"])
app.include_router(grok_router, prefix="/grok", tags=["Groq Query"])

@app.get("/")
async def root():
    return {"message": "Hello World"}