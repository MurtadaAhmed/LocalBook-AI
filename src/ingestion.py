"""
get_embedding_model(): loads the local embedding model.
get_vector_store(notebook_id: int, embedding_model=None): retrieves or create vector collection for the notebook
clear_notebook_vector_store(notebook_id: int): clears document vector for a notebook if deleted
def load_and_split_document(file_path: str): read files, extract text, and split it into chunks
add_document_to_notebook(notebook_id: int, file_path: str): processes a file and saves its vectors to the notebook's database
"""

import os
import shutil
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

os.environ["ANONYMIZED_TELEMETRY"] = "False"

CHROMA_DIR = "../storage/vector_db"

def get_embedding_model():
    """load the local embedding model"""
    print("Loading local embedding model...")
    return HuggingFaceEmbeddings(
        model_name="../models/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )

def get_vector_store(notebook_id: int, embedding_model=None):
    """retrieves or create vector collection for a notebook"""
    if embedding_model is None:
        embedding_model = get_embedding_model()

    collection_name = f"notebook_{notebook_id}"

    return Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=CHROMA_DIR,
        client_settings=Settings(
            anonymized_telemetry=False,
            is_persistent=True,
        )
    )

def clear_notebook_vector_store(notebook_id: int):
    """clears document vector for a notebook if deleted"""
    embedding_model = get_embedding_model()
    db = get_vector_store(notebook_id, embedding_model)
    try:
        db.delete_collection()
        print(f"Cleaned up vector collection for Notebook {notebook_id}")
    except Exception as e:
        print(f"Error cleaning up vector collection for Notebook {notebook_id}: {e}")

def load_and_split_document(file_path: str):
    """read files, extract text, and split it into chunks"""
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".pdf":
        loader = PyPDFLoader(file_path)
    elif file_extension in ['.txt', '.md', '.csv']:
        loader = TextLoader(file_path, encoding='utf-8')
    elif file_extension == '.docx':
        loader = Docx2txtLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)

    return chunks

def add_document_to_notebook(notebook_id: int, file_path: str):
    """processes a file and saves its vectors to the notebook's database"""
    print(f"Processing file: {os.path.basename(file_path)}...")
    chunks = load_and_split_document(file_path)

    db = get_vector_store(notebook_id)
    db.add_documents(chunks)
    print(f"Successfully added {len(chunks)} chunks to Notebook {notebook_id}.")


if __name__ == "__main__":
    print("testing ...")

    test_file = r"D:\GitHub\LocalBook-AI\test.txt"
    add_document_to_notebook(999, test_file)

