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
from settings import load_settings
import threading

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
LLM_MODEL_PATH = os.path.join(ROOT_DIR, "models", "qwen2.5-1.5b-instruct-q4_k_m.gguf")

_LLM_INSTANCE = None
_LLM_LOCK = threading.Lock()

def get_llm():
    """initialize and load local llm model"""
    global _LLM_INSTANCE
    print("Loading local LLM model (it might take a few seconds)...")

    if not os.path.exists(LLM_MODEL_PATH):
        raise FileNotFoundError(f"Model path is missing. expected it at: {LLM_MODEL_PATH}")

    user_settings = load_settings()

    with _LLM_LOCK:
        if _LLM_INSTANCE is None:
            print("Loading local LLM model into memory (First time only)...")

            if not os.path.exists(LLM_MODEL_PATH):
                raise FileNotFoundError(f"Model path is missing. expected it at: {LLM_MODEL_PATH}")

            user_settings = load_settings()

            _LLM_INSTANCE = LlamaCpp(
                model_path=LLM_MODEL_PATH,
                temperature=user_settings.get("temperature", 0.3),
                repeat_penalty=user_settings.get("repeat_penalty", 1.15),
                max_tokens=user_settings.get("max_tokens", 4096),
                n_ctx=8192,
                n_threads=os.cpu_count(),
                n_batch=512,
                n_gpu_layers=0,
                streaming=True,
                verbose=False
            )

    return _LLM_INSTANCE

def get_retriever(notebook_id: int):
    """connects to a specific notebook vector database and returns a retriever"""
    db = get_vector_store(notebook_id)
    return db.as_retriever(search_kwargs={"k": 5})

def get_conversational_chain(notebook_id: int):
    """build the rag pipeline connecting the llm, the database, and the prompts"""
    llm = get_llm()
    retriever = get_retriever(notebook_id)
    user_settings = load_settings()
    sys_prompt_string = user_settings.get("system_prompt", "")
    prompt_template = f"""
<|im_start|>system 
{sys_prompt_string}
Context:
{{context}}
<|im_end|>
<|im_start|>user
{{question}}
<|im_end|>
<|im_start|>assistant
"""
    QA_PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    condense_template = """<|im_start|>system
    Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question.
    <|im_end|>
    <|im_start|>user
    Chat History:
    {chat_history}
    Follow Up Input: {question}
    <|im_end|>
    <|im_start|>assistant
    Standalone question:"""
    CONDENSE_PROMPT = PromptTemplate(
        template=condense_template,
        input_variables=["chat_history", "question"]
    )

    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT},
        condense_question_prompt=CONDENSE_PROMPT,
        return_source_documents=True
    )

    return chain

class StreamHandler(BaseCallbackHandler):
    """catches tokens from LLM thread and puts them in a safe queue"""
    def __init__(self, queue: Queue):
        self.queue = queue
        self.stream_active = True

    def on_llm_start(self, serialized, prompts, **kwargs) -> None:
        if prompts and "Standalone question:" in prompts[0]:
            self.stream_active = False
        else:
            self.stream_active = True

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        if self.stream_active:
            self.queue.put(token)

    def on_llm_end(self, *args, **kwargs) -> None:
        if self.stream_active:
            self.queue.put(None)

    def on_llm_error(self, *args, **kwargs) -> None:
        if self.stream_active:
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

def update_llm_settings_live():
    def _reload():
        global _LLM_INSTANCE
        print("Hot-swapping AI Model with new settings...")

        with _LLM_LOCK:
            _LLM_INSTANCE = None

        get_llm()
        print("Hot-swap complete. Ready to chat")
    Thread(target=_reload, daemon=True).start()