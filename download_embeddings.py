"""a temporal file to download the embedding model from hugging face"""
from sentence_transformers import SentenceTransformer
import os

save_path = "models/all-MiniLM-L6-v2"
os.makedirs(save_path, exist_ok=True)
print("download the model..")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
model.save(save_path)
print("model saved successfully")