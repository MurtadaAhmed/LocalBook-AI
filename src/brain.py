"""
get_llm(): initialize and load local llm model
get_retriever(notebook_id: int): connects to a specific notebook vector database and returns a retriever
ask_question_stream(notebook_id: int, query: str, chat_history: list): run RAG pipeline asynchronously and yields tokens one by one
StreamHandler(BaseCallbackHandler): catches tokens from LLM thread and puts them in a safe queue
"""
import os
import torch
from langchain_community.llms import LlamaCpp
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler
from threading import Thread
from queue import Queue
from ingestion import get_vector_store
from settings import load_settings
import threading

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
LLM_MODEL_PATH = os.path.join(ROOT_DIR, "models", "Phi-3-mini-4k-instruct-q4.gguf")

_LLM_INSTANCE = None
_LLM_LOCK = threading.Lock()


def detect_gpu_layers():
    try:
        import llama_cpp
        if torch.cuda.is_available() and llama_cpp.llama_supports_gpu_offload():
            print(f"✅ CUDA detected: {torch.cuda.get_device_name(0)} — using GPU for LLM")
            return -1
    except Exception:
        pass
    print("⚠️  No CUDA GPU detected — using CPU for LLM")
    return 0

def get_llm():
    """initialize and load local llm model"""
    global _LLM_INSTANCE

    if not os.path.exists(LLM_MODEL_PATH):
        raise FileNotFoundError(f"Model path is missing. Expected it at: {LLM_MODEL_PATH}")

    with _LLM_LOCK:
        if _LLM_INSTANCE is None:
            print("Loading local LLM model into memory (First time only)...")
            user_settings = load_settings()
            _LLM_INSTANCE = LlamaCpp(
                model_path=LLM_MODEL_PATH,
                temperature=user_settings.get("temperature", 0.3),
                repeat_penalty=user_settings.get("repeat_penalty", 1.1),
                max_tokens=user_settings.get("max_tokens", 512),
                n_ctx=4096,
                n_threads=os.cpu_count(),
                n_batch=512,
                n_gpu_layers=detect_gpu_layers(),
                streaming=True,
                stop=["<|end|>", "<|endoftext|>", "<|user|>", "<|assistant|>"],
                verbose=False
            )
    return _LLM_INSTANCE


def get_retriever(notebook_id: int):
    """connects to a specific notebook vector database and returns a retriever"""
    db = get_vector_store(notebook_id)
    return db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 15}
    )


class StreamHandler(BaseCallbackHandler):
    """catches tokens from LLM thread and puts them in a safe queue"""
    def __init__(self, queue: Queue):
        self.queue = queue
        self.stream_active = True

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if self.stream_active:
            self.queue.put(token)

    def on_llm_end(self, *args, **kwargs) -> None:
        self.queue.put(None)

    def on_llm_error(self, *args, **kwargs) -> None:
        self.queue.put(None)


def ask_question_stream(notebook_id: int, query: str, chat_history: list):
    """run RAG pipeline with single LLM call and yields tokens one by one"""
    user_settings = load_settings()
    sys_prompt_string = user_settings.get("system_prompt", "")

    # Build a short history snippet from the last 1 Q&A pair only
    history_str = ""
    if chat_history:
        last_user, last_ai = chat_history[-1]
        last_ai_short = last_ai[:250] + "..." if len(last_ai) > 250 else last_ai
        history_str = f"\nPrevious exchange:\nUser: {last_user}\nAssistant: {last_ai_short}\n"

    prompt_template = f"""<|system|>
    {sys_prompt_string}{history_str}
    Use the following context to answer the question. If the answer is not in the context, say so clearly.
    Context:
    {{context}}<|end|>
    <|user|>
    {{question}}<|end|>
    <|assistant|>
    """

    QA_PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    llm = get_llm()
    retriever = get_retriever(notebook_id)

    chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type="stuff",
        chain_type_kwargs={"prompt": QA_PROMPT},
        return_source_documents=True
    )

    token_queue = Queue()
    stream_handler = StreamHandler(token_queue)
    final_result = {}

    def run_chain():
        try:
            result = chain.invoke(
                {"query": query},
                config={"callbacks": [stream_handler]}
            )
            final_result["data"] = result
        except Exception as e:
            print(f"Chain error: {e}")
            stream_handler.queue.put(None)

    llm_thread = Thread(target=run_chain)
    llm_thread.start()

    while True:
        try:
            token = token_queue.get(timeout=120)
        except Exception:
            break
        if token is None:
            break
        yield {"type": "token", "content": token}

    llm_thread.join()

    if "data" in final_result:
        yield {"type": "sources", "content": final_result["data"].get("source_documents", [])}
    else:
        yield {"type": "sources", "content": []}


def update_llm_settings_live():
    def _reload():
        global _LLM_INSTANCE
        print("Hot-swapping AI Model with new settings...")
        with _LLM_LOCK:
            _LLM_INSTANCE = None
        get_llm()
        print("Hot-swap complete. Ready to chat")
    Thread(target=_reload, daemon=True).start()
