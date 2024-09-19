import re
import ast
import numpy as np
from scipy.stats import spearmanr

# Define the ANSI escape sequence for purple
PURPLE = '\033[95m'
ENDC = '\033[0m'  # Reset to default color


def find_previous_user_query(interactions, llm_response_first_sentence):
    last_user_content = None
    for entry in interactions:
        if entry['role'] == 'user':
            last_user_content = entry['content']
        elif entry['role'] == 'assistant' and llm_response_first_sentence in entry['content']:
            return last_user_content, entry
    return None


def parse_tool_file(content, interactions):
    # Pattern to find sections with correct delimiter
    sections_pattern = r'\*\*Tool Outputs\*\*(.*?)\*\*LLM Response\*\*(.*?)(?=\*\*Tool Outputs\*\*|$)'

    # Find all matches for the sections
    matches = re.findall(sections_pattern, content, flags=re.DOTALL)

    # Process each match to extract Tool Outputs and LLM Response content
    results = []
    for match in matches:
        tool_outputs = "**Tool Outputs**\n" + match[0].strip()
        llm_response = "**LLM Response**\n" + match[1].strip()

        # Only keep the output with '----------' for evaluation
        if '----------' not in tool_outputs:
            continue  # Skip this pair

        # Separate the Instruction and Tool Outputs
        parts = tool_outputs.split('----------', 1)
        tool_outputs = parts[0].strip()
        # remainder = parts[1].strip()

        # Determine the type based on the presence of 'Title' or 'title'
        type_value = 'literature' if 'title:' in tool_outputs.lower() else 'values_and_recommendations'
        #print(f"{PURPLE}tool_outputs{ENDC}", tool_outputs, f"{PURPLE}type{ENDC}", type_value, f"{PURPLE}llm_response{ENDC}", llm_response)
        # Find previous user query that matches the first sentence of the llm_response
        first_sentence = llm_response.split('\n')[1].strip()
        previous_query, current_entry = find_previous_user_query(interactions, first_sentence)
        #print(f"{PURPLE}previous_query{ENDC}", previous_query)

        # Initialize dictionary for this pair
        entry = {
            'tool_outputs': tool_outputs,
            'llm_response': llm_response,
            'type': type_value,
            'previous_query': previous_query,
            'current_entry': current_entry
        }

        # # Extract instructions if present
        # instructions_match = re.search(r'(# Instructions:|\*\*Instructions\*\*:)(.*?)(?=\*\*LLM Response\*\*|$)', remainder, flags=re.DOTALL)
        # if instructions_match:
        #     # Save the part after '# Instructions:' or '**Instructions**:' and before '**LLM Response**'
        #     entry['instructions'] = instructions_match.group(2).strip()
        #     # print(f"{PURPLE}instructions{ENDC}", instructions_match.group(2).strip())

        results.append(entry)

    # print(results[1])
    return results


def parse_user_profile(content):
    # Initialize an empty dictionary
    user_profile = {}

    # Split the data into lines
    lines = content.split("\n")

    # Iterate over each line
    for line in lines:
        if ":" in line:  # Check if the line contains a key-value pair
            # Split the line into key and value based on the first colon
            key, value = line.split(":", 1)

            # Clean up the key and value
            key = key.strip().strip('*- ').replace("**", "").lower()  # Remove extra characters and make lowercase
            value = value.replace("**", "").strip()

            # Add the key-value pair to the dictionary
            user_profile[key] = value

    return user_profile

def parse_current_entry(entry, aspect):
    return_list = []
    if aspect == 'relevance':
        for key in range(1, 7):
            if f"relevance_feedback_q{key}" in entry.keys():
                return_list.append(entry[f"relevance_feedback_q{key}"])
            else:
                return_list.append('Not Applicable')
    elif aspect == 'accessibility':
        for key in range(1, 4):
            if f"accessibility_feedback_q{key}" in entry.keys():
                if key in [1, 3]:
                    if entry[f"accessibility_feedback_q{key}"] == 'Yes':
                        return_list.append('No')
                    elif entry[f"accessibility_feedback_q{key}"] == 'No':
                        return_list.append('Yes')
                    else:
                        return_list.append(entry[f"accessibility_feedback_q{key}"])
                else:
                    return_list.append(entry[f"accessibility_feedback_q{key}"])
            else:
                return_list.append('Not Applicable')
    elif aspect == 'entailment':
        for key in range(1, 2):
            if f"entailment_feedback_q{key}" in entry.keys():
                return_list.append(entry[f"entailment_feedback_q{key}"])
            else:
                return_list.append('Not Applicable')
    
    return return_list
            


def convert_scores(input_score, aspect):
    # Regular expression to match all reasoning blocks
    print(f"{PURPLE}response{ENDC}", input_score)
    reasonings = re.findall(r'\(\d+\)\s+(.*?)\n\n', input_score, re.DOTALL)
    # answers = re.findall(r'\*\*Answer:\*\*(.*?)\n', input_score, re.DOTALL)
    # answers = [answer.strip() for answer in answers]
    # print(f"{PURPLE}reasonings{ENDC}", reasonings)
    # print(f"{PURPLE}answers{ENDC}", answers)

    # Check if input_score is a string that contains a list
    if isinstance(input_score, str) and "[" in input_score and "]" in input_score:
        # truncate the input_score to within the brackets
        print('input_score before', input_score)
        input_score = input_score[input_score.index("["):input_score.rindex("]") + 1]
        print('input_score after', input_score)
        try:
            # Try to convert the input string to a list directly
            input_score = ast.literal_eval(input_score)
        except (ValueError, SyntaxError):
            # If that fails, apply formatting to ensure valid Python list
            # Use regex to find unquoted words (assuming words that are not numbers or surrounded by quotes)
            input_score = re.sub(r"(?<=\[|\s|,)([^\d\[\]'\"].*?)(?=,|\])", r"'\1'", input_score)

            print('input_score after formatting:', input_score)

            try:
                # Try converting again after formatting
                input_score = ast.literal_eval(input_score)
            except (ValueError, SyntaxError) as e:
                print(f"Error in converting input_score to list: {e}")
                return input_score

    # print the type of input_score to debug, use green color for debugging
    print(f"{PURPLE}input_score{ENDC}", input_score)

    if aspect in ['correctness']:
        # Check if the input data contains the format '[Num_of_Matches]/[Total_Number]'
        scores = re.findall(r"(\d+)/(\d+)", str(input_score))
        if len(scores) > 0:
            matches, total = map(int, scores[0])
        else:
            matches = total = 0

        print(f"{PURPLE}matches{ENDC}", matches, f"{PURPLE}total{ENDC}", total)

        return matches, reasonings, total, 0, input_score

    else:
        if len(input_score) == 3:   # evaluate_accessibility_in_reference
            for i in [0, 2]:
                input_score[i] = 'No' if input_score[i] == 'Yes' else 'Yes'
        return input_score, reasonings

    
if __name__ == '__main__':
    print(convert_scores("Yes, 0/8"))