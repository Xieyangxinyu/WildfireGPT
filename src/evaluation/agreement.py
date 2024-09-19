import os
import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# support colorful print
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.corpus import wordnet
lemmatizer = WordNetLemmatizer()

# Function to get part of speech tags
def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    tag = nltk.pos_tag([word])[0][1][0].upper()
    tag_dict = {"J": wordnet.ADJ, "N": wordnet.NOUN, "V": wordnet.VERB, "R": wordnet.ADV}
    return tag_dict.get(tag, wordnet.NOUN)

base_folder = "case_studies"

relevance_subcategories = ["Last Question", "Profession", "Concern", "Location", "Time", "Scope"]
accessibility_subcategories = ["No Jargon", "Enough Explanation", "No Redundancy"]

disagreement_categories = [
    "Yes vs Could be better",
    "Yes vs No",
    "Could be better vs Yes",
    "Could be better vs No",
    "No vs Yes",
    "No vs Could be better"
]

def generate_word_cloud(text, category, subcategory):
    stop_words = set(stopwords.words('english'))
    # also remove words that like "yes", "no", "could", "better" that are likely to be in the reasoning
    stop_words.update(["yes", "no", "could", "better", "be", "response", "fire", "explanation", "concern", "wildfire", "tool", "data", "question", "answer", "location", "time", "scope", "profession", "jargon", "redundancy"])
    text = ' '.join([lemmatizer.lemmatize(word, get_wordnet_pos(word)) for word in text.split()])
    try:
        wordcloud = WordCloud(width=800, height=800, background_color='white', stopwords=stop_words, min_font_size=10).generate(text)
        plt.figure(figsize=(8, 8), facecolor=None)
        plt.imshow(wordcloud)
        plt.axis("off")
        plt.tight_layout(pad=0)
        plt.savefig(f"word_clouds/{subcategory}_{category}.png")
    except ValueError:
        print(f"Error generating word cloud for {subcategory} - {category}")

def initialize_summary():
    summary = {}
    for subcategory in relevance_subcategories + accessibility_subcategories + ['entailment']:
        summary[subcategory] = {
            'agree_count': 0,
            'disagree_count': 0,
            'disagreement_categories': {category: {'count': 0, 'reasoning': []} for category in disagreement_categories}
        }
    return summary

def update_summary(summary, subcategory_df, subcategory):
    # remove rows with "Not Applicable" in human_score
    subcategory_df = subcategory_df[subcategory_df['human_score'] != "Not Applicable"]

    #if subcategory_df['input_score'] is not in ['Yes', 'No', 'Could be better']:
    if not subcategory_df['input_score'].isin(['Yes', 'No', 'Could be better']).all():
        # print in a different color to make it easier to spot
        print(f"{bcolors.WARNING}Warning: {subcategory} - {subcategory_df['input_score'].unique()} is not in ['Yes', 'No', 'Could be better']{bcolors.ENDC}")
    agree_count = (subcategory_df['human_score'] == subcategory_df['input_score']).sum()
    disagree_count = len(subcategory_df) - agree_count
    summary[subcategory]['agree_count'] += agree_count
    summary[subcategory]['disagree_count'] += disagree_count

    for category in disagreement_categories:
        score1, score2 = category.split(" vs ")
        category_df = subcategory_df[(subcategory_df['human_score'] == score1) & (subcategory_df['input_score'] == score2)]
        category_count = len(category_df)
        summary[subcategory]['disagreement_categories'][category]['count'] += category_count
        summary[subcategory]['disagreement_categories'][category]['reasoning'].extend(category_df['reasoning'].tolist())

def print_summary(summary, title):
    print(title)
    for subcategory, data in summary.items():
        agree_count = data['agree_count']
        disagree_count = data['disagree_count']
        total_count = agree_count + disagree_count
        agree_percentage = (agree_count / total_count) * 100 if total_count > 0 else 0
        disagree_percentage = (disagree_count / total_count) * 100 if total_count > 0 else 0

        print(f"{subcategory}:")
        print(f"  Agree: {agree_count} ({agree_percentage:.2f}%)")
        print(f"  Disagree: {disagree_count} ({disagree_percentage:.2f}%)")

        for category, category_data in data['disagreement_categories'].items():
            category_count = category_data['count']
            category_percentage = (category_count / disagree_count) * 100 if disagree_count > 0 else 0
            print(f"    {category}: {category_count} ({category_percentage:.2f}%)")
            print(f"      Reasoning:")
            # remove nan in reasoning
            category_data['reasoning'] = [reasoning for reasoning in category_data['reasoning'] if str(reasoning) != 'nan']
            if len(category_data['reasoning']) > 0:
                for reasoning in category_data['reasoning']:
                    print(f"        - {reasoning}")
                if "Overall" in title:
                    generate_word_cloud(" ".join(category_data['reasoning']), category, subcategory)
    print()

overall_summary = initialize_summary()

for root, dirs, files in os.walk(base_folder):
    if "evaluation copy.csv" in files:
        file_path = os.path.join(root, "evaluation.csv")
        df = pd.read_csv(file_path)

        case_summary = initialize_summary()

        relevance_df = df[df['aspect'] == 'relevance']
        for i, subcategory in enumerate(relevance_subcategories):
            subcategory_df = relevance_df.iloc[i::len(relevance_subcategories)]
            update_summary(case_summary, subcategory_df, subcategory)
            update_summary(overall_summary, subcategory_df, subcategory)

        entailment_df = df[df['aspect'] == 'entailment']
        update_summary(case_summary, entailment_df, 'entailment')
        update_summary(overall_summary, entailment_df, 'entailment')

        accessibility_df = df[df['aspect'] == 'accessibility']
        for i, subcategory in enumerate(accessibility_subcategories):
            subcategory_df = accessibility_df.iloc[i::len(accessibility_subcategories)]
            update_summary(case_summary, subcategory_df, subcategory)
            update_summary(overall_summary, subcategory_df, subcategory)

        #print_summary(case_summary, f"Summary for case study: {file_path}")

print_summary(overall_summary, "Overall summary of agreement and disagreement by subcategories summed over all case studies:")