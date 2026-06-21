import sys
import os
from importlib.metadata import metadata

SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from src.database import get_all_notebooks
from src.brain import get_retriever

def select_notebook():
    notebooks = get_all_notebooks()
    print("notebooks", notebooks)
    if not notebooks:
        print("no notebooks found in the database")
    for notebook_id, name, created_at in notebooks:
        print(f"Notebook ID {notebook_id} - Notebook Name {name} - Notebook Creation Date {created_at}")
    while True:
        try:
            choice = input("Enter a notebook ID from the result above: ")
            notebook_id_entered = int(choice)
            if any(notebook_id[0] == notebook_id_entered for notebook_id in notebooks):
                print(f"Notebook ID {notebook_id_entered} found in the database")
                return notebook_id_entered
            else:
                print("Enter a valid notebook ID.")
        except ValueError:
            print("Enter a valid notebook ID.")


def run_interactive_search():
    notebook_id = select_notebook()
    print(f"Loading the retriever for the notebook ID {notebook_id}...")
    try:
        retriever = get_retriever(notebook_id)
        print(f"Retriever loaded successfully for notebook {notebook_id}")
    except Exception as e:
        print(f"Error loading retriever for notebook ID {notebook_id}. Error: {e}")
        return
    while True:
        try:
            query = input("Search query: ")
            if not query:
                continue
            print(f"Searching for ({query}) in notebook ID {notebook_id}")
            docs = retriever.invoke(query)
            if not docs:
                print("No matching chunks found")
                continue
            print(f"Fount {len(docs)} relevant chunks")
            for index, doc in enumerate(docs, 1):
                metadata = doc.metadata
                source = os.path.basename(metadata.get("source", "Unknown Source"))
                page = metadata.get("page", "N/A")
                start_index = metadata.get("start_index", "N/A")
                print(f"Chunk #{index} | Source: {source} | Page: {page} | Start Index: {start_index}")
                print("Page Content:")
                print(doc.page_content)
        except Exception as e:
            print(f"Error during search {e}")

if __name__ == "__main__":
    run_interactive_search()