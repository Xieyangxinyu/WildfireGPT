from src.evaluation.utils import *

class Prompts:
    def __init__(self):
        pass

    def evaluate_relevance_in_reference(self, tool_output, llm_response, user_profile=None, previous_query=None):
        message = ["You are a nice evaluator. Your task is to analyze the relevance of the model's response to the contexts by answering the following questions. "
                "Please answer these questions one by one with your reasoning. Lastly, output a Python list of your responses.",
                "Given this model's response: \n" + llm_response + "\n\n"
                "(1) Does the response answer the user's last question? The question is '" + previous_query + "' Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'. Don't be too harsh.\n"
                "(2) Is the response relevant to the user's profession? The profession is '" + user_profile['profession'] + "' Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'. Don't be too harsh.\n"
                "(3) Is the response relevant to the user's concern? The concern is '" + user_profile['concern'] + "' Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'. Don't be too harsh.\n"
                "(4) Is the response relevant to the user's location? The location is '" + user_profile['location'] + "' Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'. Don't be too harsh.\n"
                "(5) Is the response relevant to the user's timeline? The timeline is '" + user_profile['time'] + "' Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'. Don't be too harsh.\n"
                "(6) Is the response relevant to the user's scope? The scope is '" + user_profile['scope'] + "' Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'. Don't be too harsh.\n"
                "Please answer these questions one by one with your reasoning. You MUST mark the response to each question in a format of (1), (2), ..., and (6).\n"
                "Lastly, output a Python list containing all your answers without reasoning or any other information.\n\n"
                ]
        return message


    def evaluate_relevance_in_values_and_recommendations(self, tool_output, llm_response, user_profile=None, previous_query=None):
        # same as evaluate_relevance_in_reference
        return self.evaluate_relevance_in_reference(tool_output, llm_response, user_profile, previous_query)


    def evaluate_correctness_in_reference(self, tool_output, llm_response, user_profile=None, previous_query=None):
        message = ["Your task has two parts, and please respond to them one after the other. "
                "The first task is to extract all the meta-information about papers mentioned in '**LLM Responses**'. "
                "You should list information such as author names, titles, DOIs, publications, and reference links (but do not include abstract) in a Python dictionary format. Use paper titles as the keys.\n"
                "The second task is to check if each paper in the dictionaries of '**LLM Responses**'can be found in the dictionary of '**Tool Outputs**.' "
                #"You should write Python code to verify each key, i.e., paper titles. "
                "That is to say, for any paper in '**LLM Responses**', verify if it exists in the dictionary of '**Tool Outputs**', "
                "and if each attribute like authors, year, doi, publication, and etc, is matched as well. "
                "Note that the author names could be rewritten in a different way. In this case, you should consider them as the same author. \n\n",

                "Following are the texts you need to analyze:\n" + tool_output + '\n' + llm_response,

                "Solely based on this LLM's response, is it true that each paper in the '**LLM Responses**' or '### References' paragraphs can be found in the '**Tool Outputs**' paragraph and all the information is correct?"
                "Provide the number of matches and the total length of the dictionary of '**LLM Responses**' by filling this answer format '[Num_of_Matches]/[Len_of_Dict]'. Do NOT provide any other responses."
                ]
        return message


    def evaluate_correctness_in_values_and_recommendations(self, tool_output, llm_response, user_profile=None, previous_query=None):
        message = ["Given information in the following '**Tool Outputs**' and '**LLM Responses**', step by step identify each important terms or nouns, "
                "and verify each numerical values in the model responses associated with these nouns. "
                "You should write down the numerical values in '**Tool Outputs**' and '**LLM Responses**' to check if they are matched.",

                "Following are the texts you need to analyze:\n\n\n" + tool_output + '\n\n' + llm_response ,

                "Solely based on this LLM's response, is it true that all important numerical value in the '**LLM Responses**' are correct?"
                "Provide the number of matches and the total number of numerical values by filling this answer format '[Num_of_Matches]/[Total_Number]'. Do NOT provide any other responses."
                ]
        return message


    def evaluate_entailment_in_reference(self, tool_output, llm_response, user_profile=None, previous_query=None):
        message = ["Your task is to list all the points stated in the **LLM Response** section, and verify with the 'Abstract' of the papers in the **Tool Outputs** section. "
                "For each point, you need to further extract only important nouns, technical terms, or facts for evaluation."
                "Think about if the analyses or recommendations in **LLM Response** are logically supported by the information in **Tool Outputs** by analyzing 1/ are there new factual information only in **LLM Response** but not in any tool outputs, and 2/ are there any contradictory information.",

                "Following are the texts you need to analyze: \n" + tool_output + '\n' + llm_response + "\nNow, please answer the following question:\n"
                "Do the analyses or recommendations in **LLM Response** logically follow from the information in **Tool Outputs**? "
                "You MUST mark the response with (1) and answer 'Yes', 'No', 'Could be better', or 'Not Applicable' with your reasoning.\n"
                "Lastly, output a Python list of your responses."
                ]
        return message


    def evaluate_entailment_in_values_and_recommendations(self, tool_output, llm_response, user_profile=None, previous_query=None):
        message = ["Your task is to list all the points stated in the **LLM Response** section, and verify with the information in the **Tool Outputs** section. "
                "For each point, you need to further extract only important nouns, technical terms, or facts for evaluation."
                "Think about if the analyses or recommendations in **LLM Response** are logically supported by the information in **Tool Outputs** by analyzing 1/ are there new factual information only in **LLM Response** but not in any tool outputs, and 2/ are there any contradictory information.",

                "Following are the texts you need to analyze: \n" + tool_output + '\n' + llm_response + "\nNow, please answer the following question:\n"
                "Do the analyses or recommendations in **LLM Response** logically follow from the information in **Tool Outputs**?  "
                "You MUST mark the response with (1) and answer 'Yes', 'No', 'Could be better', or 'Not Applicable' with your reasoning.\n"
                "Lastly, output a Python list of your responses."
                ]
        return message


    def evaluate_accessibility_in_reference(self, tool_output, llm_response, user_profile=None, previous_query=None):
        message = ["Your task is to analyze the accessibility of the model's response to the human users. "
                "For each question, always answer either 'Yes', 'No', 'Could be better', or 'Not Applicable'. Please answer these questions one by one with your reasoning. Lastly, output a Python list of your responses.",

                "Given this model's response: \n" + llm_response + "\n"
                f"(1) Does the response contain too many jargons for someone whose profession is {user_profile['profession']}? Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'.\n"
                "(2) Does the response provide enough explanation? Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'.\n"
                "(3) Does the response contain redundant or useless information? Answer 'Yes', 'No', 'Could be better', or 'Not Applicable'.\n"
                "Please answer these questions one by one with your reasoning. You MUST mark the response to each question in a format of (1), (2), and (3).\n"
                "Lastly, output a Python list of your responses."
                ]
        return message


    def evaluate_accessibility_in_values_and_recommendations(self, tool_output, llm_response, user_profile=None, previous_query=None):
        # same as evaluate_accessibility_in_reference
        return self.evaluate_accessibility_in_reference(tool_output, llm_response, user_profile, previous_query)