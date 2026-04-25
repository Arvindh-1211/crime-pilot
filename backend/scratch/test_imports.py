import time
print("Starting imports...")
start = time.time()
import google.generativeai as genai
print(f"genai took: {time.time() - start:.4f}s")

start = time.time()
from sentence_transformers import SentenceTransformer
print(f"sentence_transformers took: {time.time() - start:.4f}s")

print("Done.")
