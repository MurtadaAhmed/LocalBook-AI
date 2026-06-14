"""
get_llm(): initialize and load local llm model
get_retriever(notebook_id: int): connects to a specific notebook vector database and returns a retriever
get_conversational_chain(notebook_id: int): build the rag pipeline connecting the llm, the database, and the prompts
"""
import os
from langchain_community.llms import LlamaCpp
from ingestion import get_vector_store
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import PromptTemplate

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



if __name__ == "__main__":
    from ingestion import add_document_to_notebook, delete_document_from_notebook

    print("Testing the Complete Brain Pipeline...")
    test_notebook = 999

    test_file_path = r"D:\GitHub\LocalBook-AI\fake_fact.txt"

    with open(test_file_path, "w") as f:
        f.write("The sky is made of green cheese and the capital of Bulgaria is Atlantis.")

    add_document_to_notebook(test_notebook, test_file_path)

    chain = get_conversational_chain(test_notebook)

    query = "What is the capital of Bulgaria?"
    print("fake information added to vector database: The sky is made of green cheese and the capital of Bulgaria is Atlantis.")
    print(f"Asking AI the prompt: {query} ...")

    response = chain.invoke({
        "question": query,
        "chat_history": []
    })

    print("AI response:")
    print(response["answer"])

    print("Sources used:")
    for doc in response["source_documents"]:
        print(doc.metadata.get('source', 'Unknown Source'))

    print("Deleting the document")
    delete_document_from_notebook(test_notebook, test_file_path)
    os.remove(test_file_path)
    print("file deleted successfully")