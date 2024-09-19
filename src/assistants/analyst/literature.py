import pandas as pd
import requests

def get_doi_by_title(title):
    # URL for the Crossref API
    url = "https://api.crossref.org/works"

    # Parameters for the request, including the title to search for
    params = {"query.title": title}

    # Make the request
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()
        items = data.get("message", {}).get("items", [])

        if items:
            # Assuming the first result is the most relevant, extract its DOI
            return items[0].get("DOI")
        else:
            return "No results found"
    else:
        return "Failed to fetch data"

# Load data
df = pd.read_csv('./data/wildfire_literature.csv')
df['combined_text'] = df['title'] + ' ' + df['abstract'] + ' ' + df['field']

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


# Initialize FAISS index
index = faiss.read_index("./data/wildfire_index.bin")

# Load a sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2', device='mps')

def search(query, k=3):
    query_vector = model.encode([query]).astype(np.float32)
    _, indices = index.search(query_vector, k)
    return df.iloc[indices[0]].reset_index(drop=True)
    
def get_author(authors_str):
    import ast
    authors = ast.literal_eval(authors_str)
    if len(authors) > 3:
        # Use et al. for more than three authors
        formatted = f"{authors[0]['first']} {authors[0]['last']} et al."
    else:
        # Join all authors' names
        formatted = ', '.join(f"{author['first']} {author['last']}" for author in authors)
    return formatted

def literature_search(query, messages = None):
    '''
    input: 
        query: the query to search for. For example, 'What is the relationship between climate change and wildfire?'
    output:
        a string containing the titles and abstracts of the 3 most relevant papers
    '''
    results = search(query).to_dict('records')
    for _, result in enumerate(results):
        result['doi'] = get_doi_by_title(result['title'])
        # check if title of doi matches title of result
        if result['doi'] != 'No results found' and result['doi'] != 'Failed to fetch data':
            # use crossref to get the title of the doi
            url = f"https://api.crossref.org/works/{result['doi']}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                title = data.get("message", {}).get("title", [])
                if title:
                    # use model to check if title matches
                    title = title[0]
                    title_vector = model.encode([title]).astype(np.float32)
                    result_vector = model.encode([result['title']]).astype(np.float32)
                    similarity = np.dot(title_vector, result_vector.T)

                    # check if author matches
                    author = data.get("message", {}).get("author", [])
                    if author:
                        try:
                            author = author[0]['family']
                        except:
                            author = author[0]['name']
                        if author.lower() not in result['authors'].lower():
                            similarity = 0
                    if similarity < 0.8:
                        result['doi'] = 'No results found'
                    else:
                        result['doi'] = f"https://doi.org/{result['doi']}"
            else:
                result['doi'] = 'Failed to fetch data'
    
    message = f"Here are the 3 most relevant papers for your query '{query}':\n\n"
    for i, result in enumerate(results):
        message += f"{i+1}. Title: {result['title']}\n"
        message += f"Authors: {get_author(result['authors'])}\n"
        message += f"Year: {result['year']}\n"
        if result['doi'] != 'No results found' and result['doi'] != 'Failed to fetch data':
            message += f"DOI: {result['doi']}\n"
        message += f"Abstract: {result['abstract']}\n\n"
        
    return message

if __name__ == "__main__":
    query = "wildfire mitigation strategies for bridge construction in wildfire-prone areas"
    results = literature_search(query)
    print(results)