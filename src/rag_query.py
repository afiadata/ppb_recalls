import os
import requests
from typing import Optional, List, Any 
from dotenv import load_dotenv

from pydantic import BaseModel 
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores.pgvector import PGVector
from langchain.chains import RetrievalQA
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models import LLM

# --- Load .env and validate env vars ---
load_dotenv()

PGVECTOR_CONNECTION_STRING = (
    f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)


CONNECTION_STRING = os.getenv("PGVECTOR_CONNECTION_STRING")
REMOTE_LLM_API_URL = os.getenv("REMOTE_LLM_API_URL")

if not CONNECTION_STRING:
    raise ValueError("Missing PGVECTOR_CONNECTION_STRING in .env")

if not REMOTE_LLM_API_URL:
    raise ValueError("Missing REMOTE_LLM_API_URL in .env")

# --- Set up the embedding model ---
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# --- Load retriever ---
retriever = PGVector(
    connection_string=CONNECTION_STRING,
    embedding_function=embedding_model,
    collection_name="rag_collection"
).as_retriever(search_kwargs={"k": 5})


# --- Custom Remote LLM class ---
class RemoteLLM(LLM):
    api_url: str

    def _call(self, prompt: str, stop: Optional[List[str]] = None,
              run_manager: Optional[CallbackManagerForLLMRun] =None, 
              **kwargs: Any) -> str:
        try:
            response = requests.post(
                self.api_url,
                json={'prompt': prompt},
                timeout=10  # timeout added
            )
            response.raise_for_status()
            return response.json().get('response', "No response field in JSON")
        except Exception as e:
            return f"[Error calling remote LLM] {str(e)}"

    @property
    def _identifying_params(self):
        return {'api_url': self.api_url}

    @property
    def _llm_type(self) -> str:
        return "remote_llm"


# --- Instantiate the remote LLM and QA pipeline ---
remote_llm = RemoteLLM(api_url=REMOTE_LLM_API_URL)

qa = RetrievalQA.from_chain_type(
    llm=remote_llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True
)

# --- Colab-friendly query interface ---
def run_query(query: str, print_sources: bool = True):
    result = qa(query)
    print("🔍 Query:", query)
    print("✅ Answer:", result['result'])

    if print_sources:
        print("\n📄 Source Documents Metadata:")
        for i, doc in enumerate(result['source_documents']):
            print(f"  [{i+1}] {doc.metadata}")

        print("\n📄 Source Texts:")
        for i, doc in enumerate(result['source_documents']):
            print(f"\n--- Source {i+1} ---\n{doc.page_content}")

        print(f"\n📊 Retrieved {len(result['source_documents'])} documents")

# --- Run in Colab ---
