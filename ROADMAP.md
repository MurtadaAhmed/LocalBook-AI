
## 🏗️ LocalBook AI:

### Core Architecture Summary

* **Target OS:** Windows (Portable Desktop App)
* **Python Version:** 3.11.x (Strictly avoid 3.12+ for C++ binding stability)
* **UI Framework:** Flet (Asynchronous Desktop GUI)
* **Local LLM:** Qwen2.5-1.5B-Instruct-Q4_K_M.gguf (via llama-cpp-python)
* **Embeddings:** all-MiniLM-L6-v2 (via sentence-transformers)
* **Databases:** ChromaDB (Vector/Documents) & SQLite (Chat History)

---

### Phase 0: Environment & Foundation

**Goal:** Lock in all dependencies and prepare the physical folder structure so the application runs predictably.

* **Step 0.1: Install Python 3.11:** Ensure it is installed and added to your system PATH.
* **Step 0.2: Initialize the Repository:** Create your root folder (`LocalBook_AI`), set up version control (`git init`), and create a `.gitignore` file (ignoring `venv/`, `__pycache__/`, `models/`, and `storage/`).
* **Step 0.3: Build the Directory Structure:** Create the following empty folders in the root directory: `src/`, `models/`, and `storage/`. Inside `storage/`, create a `vector_db/` folder.
* **Step 0.4: Lock Dependencies:** Create `requirements.txt` containing exact versions (`flet==0.22.0`, `langchain==0.1.16`, `langchain-community==0.0.34`, `llama-cpp-python==0.2.62`, `sentence-transformers==2.7.0`, `chromadb==0.4.24`, `pypdf==4.2.0`).
* **Step 0.5: Set up Virtual Environment:** Run `python -m venv venv`, activate it, and run `pip install -r requirements.txt`.
* **Step 0.6: Download the Brain:** Download the `qwen2.5-1.5b-instruct-q4_k_m.gguf` file from Hugging Face and place it explicitly inside the `models/` directory.

---

### Phase 1: The SQLite Database Layer (`src/database.py`)

**Goal:** Build the system that remembers user workspaces (Notebooks) and their conversational history.

* **Step 1.1: Database Connection:** Write a function to initialize a connection to `storage/chat_history.db` using Python's built-in `sqlite3` library.
* **Step 1.2: Table Schema Setup:** Execute SQL commands to create two tables. Table 1 is `notebooks` (Columns: `id`, `name`, `created_at`). Table 2 is `messages` (Columns: `id`, `notebook_id`, `role`, `content`, `timestamp`).
* **Step 1.3: Notebook Management Logic:** Create Python functions to `create_notebook()`, `get_all_notebooks()`, and `delete_notebook()`.
* **Step 1.4: Chat History Logic:** Create Python functions to `save_message(notebook_id, role, content)` and `get_messages_by_notebook(notebook_id)`.

---

### Phase 2: Document Ingestion Pipeline (`src/ingestion.py`)

**Goal:** Read user files, chop them into readable chunks, and save them as mathematical vectors.

* **Step 2.1: Initialize Embeddings:** Load `HuggingFaceEmbeddings` using the `all-MiniLM-L6-v2` model.
* **Step 2.2: Initialize Persistent ChromaDB:** Set up the ChromaDB client to save data directly to the `storage/vector_db/` folder.
* **Step 2.3: Document Loading & Splitting:** Write a function using LangChain's `PyPDFLoader` and `TextLoader`. Route the output through the `RecursiveCharacterTextSplitter` (e.g., chunk size of 1000, overlap of 200).
* **Step 2.4: Metadata Extraction:** Ensure the chunking logic captures the original `filename` and `page_number` and assigns them to the chunk's metadata dictionary.
* **Step 2.5: Vector Insertion:** Write a function that takes a Notebook Name, creates or retrieves a ChromaDB collection with that exact name, and inserts the embedded document chunks into it.
* **Step 2.6: File Management:** Create a helper function to list all unique files currently stored in a specific Notebook's collection and a function to delete a file's vectors if the user removes it.

---

### Phase 3: RAG Orchestration & The AI Brain (`src/brain.py`)

**Goal:** Connect the user's prompt, the historical chat context, the database search, and the local AI model.

* **Step 3.1: Model Initialization:** Instantiate LangChain's `LlamaCpp` class pointing to the `.gguf` file in the `models/` folder. Set `n_ctx=4096` (context window), `n_threads=4` (to protect hardware limits), and `streaming=True`.
* **Step 3.2: Retrieval Configuration:** Write a function that takes a Notebook ID, grabs the corresponding ChromaDB collection, and configures it as a LangChain Retriever (e.g., fetching the top 3 most relevant chunks).
* **Step 3.3: Strict System Prompts:** Define the core prompt template instructing the AI to act strictly as a data assistant that must cite sources and refuse to answer if the context is missing.
* **Step 3.4: Conversational Chain Setup:** Build a memory-aware LCEL (LangChain Expression Language) pipeline or use `ConversationalRetrievalChain`. It must first condense the chat history and new question into a standalone query, search the vector DB, and pass the context to the model.
* **Step 3.5: Async Generator:** Wrap the model invocation in an asynchronous Python generator (`yield`) so the Flet UI can capture text chunks in real-time as they are produced.

---

### Phase 4: Asynchronous User Interface (`src/main.py`)

**Goal:** Build the desktop application window, the active workspace dashboard, and the chat UI.

* **Step 4.1: App Initialization:** Set up the base Flet `page` (Title: LocalBook AI, Theme: Dark Mode, Layout: row-based split screen).
* **Step 4.2: Left Sidebar (Notebooks):** Create a column containing an "Add Notebook" button and a `ListView` of existing Notebooks. Tie clicks to the `database.py` fetching logic to update the main screen.
* **Step 4.3: Right Panel (Chat & Input):** Build a scrollable `ListView` for the chat history and a bottom row containing a `TextField` for user input and a `FilePicker` button for document uploads.
* **Step 4.4: Active Workspace Dashboard:** Create a small UI panel that dynamically displays the names of the PDFs/files currently embedded in the active Notebook (using the function from Step 2.6).
* **Step 4.5: Wiring the Async Stream:** When the user sends a message, append a "User" text bubble. Append a blank "AI" text bubble. Call the async generator from `brain.py`. As tokens `yield`, append them to the AI text bubble and call `page.update()` to create the typewriter effect.
* **Step 4.6: Source Citation Badges:** Modify the AI text bubble UI component to render clickable or distinct visual badges at the bottom containing the `filename` and `page_number` retrieved during the LangChain process.

---

### Phase 5: Final Testing & Portable Packaging

**Goal:** Ensure the app works seamlessly offline and structure it for easy distribution.

* **Step 5.1: The Airplane Mode Test:** Turn off Wi-Fi on your development machine. Create a new notebook, upload a PDF, and ask a complex question to ensure zero external API calls are being made.
* **Step 5.2: Directory Cleanup:** Ensure `storage/vector_db/` and `storage/chat_history.db` are cleared of any test data.
* **Step 5.3: Creation of the Portable Zip:** Create a batch script or manually zip the `src/`, `models/`, and empty `storage/` folders along with a simple `run.bat` file (which activates the environment and runs `python src/main.py`).