from sentence_transformers import SentenceTransformer
import torch

sbert_model = SentenceTransformer('all-MiniLM-L6-v2')
cossim = torch.nn.CosineSimilarity(dim=0, eps=1e-6)

def score_sbert_similarity(text1, text2):
    embeddings = sbert_model.encode([text1, text2], convert_to_tensor=True)
    return cossim(embeddings[0], embeddings[1]).item()