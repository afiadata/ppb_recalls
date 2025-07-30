import os
import logging
import argparse
from typing import List

from tqdm import tqdm
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.pgvector import PGVector
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Load environment variables
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
    """Load a PDF file and split it into chunks."""
    loader = PyPDFLoader(file_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    for chunk in chunks:
        chunk.metadata['source'] = os.path.basename(file_path)

    return chunks


def ingest_pdfs_to_pgvector(pdf_folder: str) -> None:
    """Ingest PDF documents from a folder into PGVector."""
    if not os.path.exists(pdf_folder):
        raise FileNotFoundError(f"PDF folder not found: {pdf_folder}")

    pdf_files = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    if not pdf_files:
        logging.warning(f"No PDF files found in {pdf_folder}")
        return

    all_chunks = []
    logging.info(f"Found {len(pdf_files)} PDF files in {pdf_folder}")

    for filename in tqdm(pdf_files, desc="Processing PDFs"):
        try:
            chunks = load_and_split_pdf(os.path.join(pdf_folder, filename))
            all_chunks.extend(chunks)
        except Exception as e:
            logging.error(f"Failed to process {filename}: {e}")

    if not all_chunks:
        logging.warning("No chunks to ingest.")
        return

    logging.info(f"Ingesting {len(all_chunks)} chunks into the vector store...")
    try:
        PGVector.from_documents(
            documents=all_chunks,
            embedding=embeddings,
            connection_string=CONNECTION_STRING,
            collection_name="recalls_pdf_chunks",
            collection_config={"distance_strategy": "COSINE"}
        )
        logging.info("Ingestion complete.")
    except Exception as e:
        logging.error(f"Error during ingestion to PGVector: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest PDF documents into PGVector.")
    parser.add_argument(
        "--folder",
        type=str,
        required=True,
        help="Path to the folder containing PDF files"
    )
    args = parser.parse_args()

    ingest_pdfs_to_pgvector(pdf_folder=args.folder) 

    

