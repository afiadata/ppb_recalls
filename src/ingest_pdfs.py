import os
import logging
from typing import List

from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.pgvector import PGVector
from langchain.embeddings import HuggingFaceEmbeddings
from dotenv import load_dotenv
from langchain.docstore.document import Document

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


load_dotenv()

# Validate
required_envs = ["DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME"]
missing = [var for var in required_envs if not os.getenv(var)]
if missing:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

CONNECTION_STRING = (
    f'postgresql+psycopg2://{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}'
    f'@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}'
)

# Initialize embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")

def load_and_split_pdf(file_path: str) -> List[Document]:
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    for chunk in chunks:
        chunk.metadata['source'] = os.path.basename(file_path)

    return chunks

def ingest_pdfs_to_pgvector(pdf_folder: str) -> None:
    if not os.path.exists(pdf_folder):
        raise FileNotFoundError(f"PDF folder not found: {pdf_folder}")

    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    if not pdf_files:
        logging.warning(f"No PDF files found in {pdf_folder}")
        return

    all_chunks = []
    for filename in pdf_files:
        try:
            logging.info(f"Processing {filename}")
            chunks = load_and_split_pdf(os.path.join(pdf_folder, filename))
            all_chunks.extend(chunks)
        except Exception as e:
            logging.error(f"Failed to process {filename}: {e}")

    if not all_chunks:
        logging.warning("No chunks to ingest.")
        return

    logging.info(f"Ingesting {len(all_chunks)} chunks into the vector store...")
    PGVector.from_documents(
        documents=all_chunks,
        embeddings=embeddings,
        connection_string=CONNECTION_STRING,
        collection_name="recalls_pdf_chunks",
        collection_config={"distance_strategy": "cosine"}  # Optional
    )
    logging.info("Ingestion complete.")

if __name__ == "__main__":
    ingest_pdfs_to_pgvector(pdf_folder="./data/recalls_pdf")

    

