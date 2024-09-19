import pandas as pd
import pickle

# Load data
df = pd.read_csv('./data/wildfire_literature.csv')
df['combined_text'] = df['title'] + ' ' + df['abstract'] + ' ' + df['field']

from sentence_transformers import SentenceTransformer

# Load a sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2', device='mps')

# Encode documents
document_embeddings = model.encode(df['combined_text'].tolist(), show_progress_bar=True)

pickle.dump(document_embeddings, open('./data/document_embeddings.pkl', 'wb'))