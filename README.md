# LocalBook-AI (in progress)
LocalBook AI is a 100% private, offline desktop application that lets you chat directly with your own documents. Whether you are organizing business process guidelines, team training manuals, or university computer science lectures, this tool reads your files and answers your questions instantly without ever connecting to the internet.

Most AI tools require you to upload your personal files to the cloud. LocalBook AI is completely self-sufficient and runs directly on your computer. 

* **100% Offline & Private:** Your files never leave your hard drive. The AI "brain" is downloaded once and lives right on your computer.
* **Always Remembers (Workspaces):** Create different "Notebooks" for different topics. The app remembers your past conversations in each specific notebook.
* **Shows Its Math:** When the AI answers a question, it points you exactly to the file and page number it got the information from, so you never have to guess if it is making things up.

This app is built to be lightweight and fast, even on standard laptops:
* **The Interface:** Built with a simple, modern design that feels like a standard chat app.
* **The Reader:** Uses a highly efficient, free tool (`all-MiniLM-L6-v2`) to read and organize your documents locally.
* **The AI Brain:** Powered by an optimized, small-sized AI model (Qwen 1.5B) that is smart enough to understand complex documents but light enough to not slow down your computer.

When you download the project, the files are organized like this:

```text
LocalBook_AI/
├── src/
│   ├── main.py             
│   ├── ingestion.py        
│   ├── brain.py            
│   └── database.py         
├── models/                 
├── storage/                
├── .env.example            
├── .gitignore               
└── requirements.txt        
```
