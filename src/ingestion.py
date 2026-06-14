"""
get_embedding_model(): loads the local embedding model.
get_vector_store(notebook_id: int, embedding_model=None): retrieves or create vector collection for the notebook
clear_notebook_vector_store(notebook_id: int): clears document vector for a notebook if deleted
load_and_split_document(file_path: str): read files, extract text, and split it into chunks
add_document_to_notebook(notebook_id: int, file_path: str): processes a file and saves its vectors to the notebook's database
get_notebook_files(notebook_id: int): scan the database and returns a list of unique file paths stored in the notebook
delete_document_from_notebook(notebook_id: int, file_path: str): finds all document chunks from a specific file path and delete them from vector database
"""

import os
import shutil
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from chromadb.config import Settings
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

os.environ["ANONYMIZED_TELEMETRY"] = "False"

_EMBEDDING_MODEL = None

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)

CHROMA_DIR = os.path.join(ROOT_DIR, "storage", "vector_db")
EMBEDDING_MODEL_PATH = os.path.join(ROOT_DIR, "models", "all-MiniLM-L6-v2")

def get_embedding_model():
    """load the local embedding model"""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        print("Loading local embedding model (Global Init)...")
        _EMBEDDING_MODEL = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL_PATH,
            model_kwargs={'device': 'cpu'}
        )
    return _EMBEDDING_MODEL

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

def get_notebook_files(notebook_id: int):
    """scan the database and returns a list of unique file paths stored in the notebook"""
    db = get_vector_store(notebook_id)

    results = db.get(include=["metadatas"])

    unique_files = set()

    for metadata in results.get("metadatas", []):
        if metadata and "source" in metadata:
            unique_files.add(metadata['source'])
    return list(unique_files)

def delete_document_from_notebook(notebook_id: int, file_path: str):
    """finds all document chunks from a specific file path and delete them from vector database"""
    db = get_vector_store(notebook_id)

    try:
        db._collection.delete(where={"source": file_path})
        print(f"successfully deleted vectors for: {os.path.basename(file_path)}")
    except Exception as e:
        print(f"Error deleting document: {e}")


if __name__ == "__main__":
    print("testing ...")

    test_file = r"D:\GitHub\LocalBook-AI\test.txt"
    test_notebook = 999

    add_document_to_notebook(test_notebook, test_file)
    print("finding files in the current notebook 999")
    files = get_notebook_files(test_notebook)
    for f in files:
        print(os.path.basename(f))

    print("delete the file")
    delete_document_from_notebook(test_notebook, test_file)

    print("files in notebook 999 after deletion")
    files_after = get_notebook_files(test_notebook)
    if not files_after:
        print("notebook is completely empty")
    else:
        print("files still remain: ", files_after)

