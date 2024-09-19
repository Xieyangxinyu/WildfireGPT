import faiss
import numpy as np
import pickle

# Convert embeddings to float32 for FAISS
document_embeddings = pickle.load(open('./data/document_embeddings.pkl', 'rb'))
document_embeddings = document_embeddings.astype(np.float32)

# Initialize FAISS index
d = document_embeddings.shape[1]  # Dimension of vectors
index = faiss.IndexFlatL2(d)  # Using the L2 distance metric
index.add(document_embeddings)  # Add vectors to the index
faiss.write_index(index, './data/wildfire_index.bin')

