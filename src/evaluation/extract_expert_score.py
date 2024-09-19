import json
from src.evaluation.utils import parse_current_entry
import numpy as np

score_map = {
    "Yes": 1,
    "No": 0,
    "Could be better": 0.5,
    "Not Applicable": None
}

def score_formatting(sum_, length):
    return f"{sum_/length:.4f}({sum_}/{length})"

def extract_expert_score(interaction_history):
    expert_score = {
        "relevance": {
            "last_question": [],
            "profession": [],
            "concern": [],
            "location": [],
            "time": [],
            "scope": []
        },
        "entailment": [],
        "accessibility": {
            "No Jargon": [],
            "Enough Explanation": [],
            "No Redundancy": []
        }
    }

    for aspect in expert_score.keys():
        for entry in interaction_history:
            parsed_entry = parse_current_entry(entry, aspect)
            # remove 'Not Applicable' from the list
            parsed_entry = [score_map[x] for x in parsed_entry]
            if aspect == 'relevance':
                for key, value in zip(expert_score[aspect].keys(), parsed_entry):
                    if value is not None:
                        expert_score[aspect][key].append(value)
            elif aspect == 'accessibility':
                for key, value in zip(expert_score[aspect].keys(), parsed_entry):
                    if value is not None:
                        expert_score[aspect][key].append(value)
            elif parsed_entry[0] is not None:
                expert_score[aspect] += parsed_entry

    print_message = f"Expert scores:\nRelevance:\nLast Question: {score_formatting(sum(expert_score['relevance']['last_question']), len(expert_score['relevance']['last_question']))}\nProfession: {score_formatting(sum(expert_score['relevance']['profession']), len(expert_score['relevance']['profession']))}\nConcern: {score_formatting(sum(expert_score['relevance']['concern']), len(expert_score['relevance']['concern']))}\nLocation: {score_formatting(sum(expert_score['relevance']['location']), len(expert_score['relevance']['location']))}\nTime: {score_formatting(sum(expert_score['relevance']['time']), len(expert_score['relevance']['time']))}\nScope: {score_formatting(sum(expert_score['relevance']['scope']), len(expert_score['relevance']['scope']))}\nEntailment: {score_formatting(sum(expert_score['entailment']), len(expert_score['entailment']))}\nAccessibility:\nNo Jargon: {score_formatting(sum(expert_score['accessibility']['No Jargon']), len(expert_score['accessibility']['No Jargon']))}\nEnough Explanation: {score_formatting(sum(expert_score['accessibility']['Enough Explanation']), len(expert_score['accessibility']['Enough Explanation']))}\nNo Redundancy: {score_formatting(sum(expert_score['accessibility']['No Redundancy']), len(expert_score['accessibility']['No Redundancy']))}"



    print(print_message)
    return expert_score

def extract_correctness_score(data_dict):
    score_dict = {
        "data analysis": {
            "total_count": [],
            "total_score": []
        },
        "literature review": {
            "total_count": [],
            "total_score": [],
            "sbert_score": [],
            "rouge_score": {
                "rouge-1": [],
                "rouge-2": [],
                "rouge-l": []
            }
        }
    }

    for entry in data_dict:
        if "sbert_score" in entry["auto_score"].keys():
            score_dict["literature review"]["sbert_score"].append(entry["auto_score"]["sbert_score"])
            score_dict["literature review"]["total_count"].append(entry["manual_score"]["total_count"])
            score_dict["literature review"]["total_score"].append(entry["manual_score"]["total_score"])
        else:
            if entry["manual_score"]["total_count"] != 0:
                score_dict["data analysis"]["total_count"].append(entry["manual_score"]["total_count"])
                score_dict["data analysis"]["total_score"].append(entry["manual_score"]["total_score"])

    print_message = "Correctness scores:"
    if len(score_dict["data analysis"]["total_count"]) > 0 and sum(score_dict["data analysis"]["total_count"]) > 0:
        print_message += f"\nData analysis: {score_formatting(sum(score_dict['data analysis']['total_score']), sum(score_dict['data analysis']['total_count']))}"
    if len(score_dict["literature review"]["total_count"]) > 0 and sum(score_dict["literature review"]["total_count"]) > 0:
        print_message += f"\nLiterature review: {score_formatting(sum(score_dict['literature review']['total_score']), sum(score_dict['literature review']['total_count']))}"
        print_message += f"\nSBERT: {(np.mean(score_dict['literature review']['sbert_score']), len(score_dict['literature review']['sbert_score']))}"
    
    print(print_message)

# read case_studies folder, all folders in it
# for each folder, read interaction.jsonl
# extract expert scores

import os
case_studies_folder = "case_studies/"

for case in os.listdir(case_studies_folder):
    if os.path.isdir(os.path.join(case_studies_folder, case)):
        with open(os.path.join(case_studies_folder, case, "interaction.jsonl"), 'r') as interaction_file:
            interaction_history = []
            for line in interaction_file:
                interaction_history.append(json.loads(line))
        print(f"Case: {case}")
        expert_score = extract_expert_score(interaction_history)