"""
get_llm(): initialize and load local llm model
get_retriever(notebook_id: int): connects to a specific notebook vector database and returns a retriever
get_conversational_chain(notebook_id: int): build the rag pipeline connecting the llm, the database, and the prompts
ask_question_stream(notebook_id: int, query: str, chat_history: list): run RAG chain asynchronously and yields tokens one by one
StreamHandler(BaseCallbackHandler): catches tokens from LLM thread and puts them in a safe queue
"""
import os
from langchain_community.llms import LlamaCpp
from ingestion import get_vector_store
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from threading import Thread
from queue import Queue
import time

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
LLM_MODEL_PATH = os.path.join(ROOT_DIR, "models", "qwen2.5-1.5b-instruct-q4_k_m.gguf")

def get_llm():
    """initialize and load local llm model"""
    print("Loading local LLM model (it might take a few seconds)...")

    if not os.path.exists(LLM_MODEL_PATH):
        raise FileNotFoundError(f"Model path is missing. expected it at: {LLM_MODEL_PATH}")


    llm = LlamaCpp(
        model_path=LLM_MODEL_PATH,
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

def get_conversational_chain(notebook_id: int):
    """build the rag pipeline connecting the llm, the database, and the prompts"""
    llm = get_llm()
    retriever = get_retriever(notebook_id)

    prompt_template = """
<|im_start|>system Your are a strict data assistant. Use ONLY the following provided context to answer the user's question.
If the answer is not contained in the context, you must reply exactly with: "I cannot find this information in the notebook." 
Do not use outside knowledge. Do not hallucinate.
Context:
{context}
<|im_end|>
<|im_start|>user
{question}
<|im_end|>
<|im_start|>assistant
"""
    QA_PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT},
        return_source_documents=True
    )

    return chain

class StreamHandler(BaseCallbackHandler):
    """catches tokens from LLM thread and puts them in a safe queue"""
    def __init__(self, queue: Queue):
        self.queue = queue

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        self.queue.put(token)

    def on_llm_end(self, *args, **kwargs) -> None:
        self.queue.put(None)

    def on_llm_error(self, *args, **kwargs) -> None:
        self.queue.put(None)


def ask_question_stream(notebook_id: int, query: str, chat_history: list):
    """run RAG chain asynchronously and yields tokens one by one"""
    chain = get_conversational_chain(notebook_id)
    token_queue = Queue()
    stream_handler = StreamHandler(token_queue)

    final_result = {}

    def run_chain():
        result = chain.invoke(
            {"question": query, "chat_history": chat_history},
            config={"callbacks": [stream_handler]}
        )

        final_result["data"] = result

    llm_thread = Thread(target=run_chain)
    llm_thread.start()

    while True:
        token = token_queue.get()
        if token is None:
            break
        yield {"type": "token", "content": token}

    llm_thread.join()

    yield {"type": "sources", "content": final_result["data"]["source_documents"]}


if __name__ == "__main__":
    from ingestion import add_document_to_notebook, delete_document_from_notebook

    print("Testing Thread-Safe Streaming Pipeline...")
    test_notebook = 999
    test_file_path = r"D:\GitHub\LocalBook-AI\fake_fact.txt"

    # 1. Setup a much longer fake document
    with open(test_file_path, "w") as f:
        f.write(
            "Atlantis is the capital of Bulgaria. It is a beautiful underwater city "
            "where citizens commute by riding trained dolphins. The traditional food "
            "is a deep-sea kelp burger, and the mayor is a giant seahorse named Charles."
        )
    add_document_to_notebook(test_notebook, test_file_path)

    query = "Describe the capital of Bulgaria in detail."
    print(f"\nAsking AI: '{query}'")
    print("Response stream: ", end="", flush=True)

    # 2. Iterate through the synchronous generator
    for chunk in ask_question_stream(test_notebook, query, []):
        if chunk["type"] == "token":
            print(chunk["content"], end="", flush=True)
            time.sleep(0.05) # Artificially slow down the terminal for the typewriter effect
        elif chunk["type"] == "sources":
            print("\n\n--- Sources ---")
            for doc in chunk["content"]:
                print(doc.metadata.get('source', 'Unknown Source'))

    # 3. Cleanup
    print("\nDeleting the document...")
    delete_document_from_notebook(test_notebook, test_file_path)
    os.remove(test_file_path)
    print("Test complete.")