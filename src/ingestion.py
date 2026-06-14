"""
get_embedding_model(): loads the local embedding model.
get_vector_store(notebook_id: int, embedding_model=None): retrieves or create vector collection for the notebook
"""

import os
import shutil
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings

CHROMA_DIR = "storage/vector_db"

def get_embedding_model():
    """load the local embedding model"""
    print("Loading local embedding model...")
    return HuggingFaceEmbeddings(
        model_name="./models/all-MiniLM-L6-v2",
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
        persist_directory=CHROMA_DIR
    )



def clear_notebook_vector_store(notebook_id: int):
    ...

