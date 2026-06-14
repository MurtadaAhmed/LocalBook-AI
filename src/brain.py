"""
get_llm(): initialize and load local llm model
get_retriever(notebook_id: int): connects to a specific notebook vector database and returns a retriever
"""
import os
from langchain_community.llms import LlamaCpp
from ingestion import get_vector_store

def get_llm():
    """initialize and load local llm model"""
    print("Loading local LLM model (it might take a few seconds)...")

    model_path = "../models/qwen2.5-1.5b-instruct-q4_k_m.gguf"

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model path is missing. expected it at: {model_path}")

    llm = LlamaCpp(
        model_path=model_path,
        temperature=0.1,
        n_ctx=4096, # context window size
        n_threads=4, # number of threads
        max_tokens=512, # maximum for AI response
        streaming=True, # for real-time effect in UI
        verbose=False # disable c++ diagnostic logs
    )

    return llm

def get_retriever(notebook_id: int):
    """connects to a specific notebook vector database and returns a retriever"""
    db = get_vector_store(notebook_id)
    return db.as_retriever(search_kwargs={"k": 3})


if __name__ == "__main__":
    llm = get_llm()
    print("model loaded successfully")

    prompt = "'What is the capital city of Bulgaria?"
    print(f"testing with prompt: {prompt}")
    response = llm.invoke(prompt)
    print("response:")
    print(response)


