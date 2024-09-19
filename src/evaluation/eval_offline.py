import torch
from tqdm import tqdm
import json
import argparse
import yaml
from src.evaluation.utils import parse_tool_file, parse_user_profile, convert_scores, parse_current_entry
from src.evaluation.prompts import Prompts
from src.config import client
from src.evaluation.auto import score_sbert_similarity
import pandas as pd
import streamlit as st


class Evaluator:
    def __init__(self, args):
        self.args = args
        self.prompts = Prompts()
        self.case = args['case_folder']

        # Load the file to evaluate
        # combine path to the case folder with the file name
        with open(f"{self.case}/interaction.jsonl", 'r') as interaction_file:
            self.interaction_history = []
            for line in interaction_file:
                self.interaction_history.append(json.loads(line))

        with open(f"{self.case}/tools.txt", 'r', encoding='utf-8') as file:
            content = file.read()
            self.data_dict = parse_tool_file(content, self.interaction_history)

        with open(f"{self.case}/user_profile.txt", 'r') as user_profile_file:
            content = user_profile_file.read()
            self.user_profile = parse_user_profile(content)

        # Initialize overall scores
        self.scores = {'relevance_score': 0, 'correctness_score': 0, 'entailment_score': 0, 'accessibility_score': 0,
                       'relevance_total': 0, 'correctness_total': 0, 'entailment_total': 0, 'accessibility_total': 0,
                       'relevance_na': 0, 'correctness_na': 0, 'entailment_na': 0, 'accessibility_na': 0}

    def init_assistant(self, messages, model='gpt-4-turbo'):
        # Each evaluation is a separate thread
        assistant = client.beta.assistants.create(
            name="Response Evaluator",
            model=model,
            instructions=messages[0],
            # tools=[{"type": "code_interpreter"}]
        )

        thread = client.beta.threads.create()
        return assistant, thread

    def query_assistant(self, assistant_id, thread_id, content, tools_on=False):

        message = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=content,
        )
        if tools_on:
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=assistant_id,
                tools=[{"type": "code_interpreter"}]
            )
        else:
            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread_id,
                assistant_id=assistant_id,
            )

        if run.status == 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=thread_id
            )
            # print(messages.data[0].content[0].text.value)
            return messages.data[0].content[0].text.value
        else:
            # print(run.status)
            return None

    def evaluate_single_aspect(self, tool_outputs, llm_response, data_type, previous_query, aspect):
        if data_type == 'literature':
            messages = getattr(self.prompts, f'evaluate_{aspect}_in_reference')(tool_outputs, llm_response, self.user_profile, previous_query)
        else:
            messages = getattr(self.prompts, f'evaluate_{aspect}_in_values_and_recommendations')(tool_outputs, llm_response, self.user_profile, previous_query)

        assistant, thread = self.init_assistant(messages[0], self.args['llm_model'])
        response = self.query_assistant(assistant.id, thread.id, messages[1], tools_on=False)
        if response is not None and len(messages) > 2:
            response = self.query_assistant(assistant.id, thread.id, messages[2], tools_on=False)
        return response

    @staticmethod
    def update_score(i, field):
        data = st.session_state['data_dict'][i]
        data["manual_score"][field] = st.session_state[f"{i}_{field}"]

    def manual_evaluate(self):
        st.title("Manual Evaluation")

        if 'data_dict' not in st.session_state:
            with open(f'{self.case}/data_dict.json', 'r') as f:
                st.session_state['data_dict'] = json.load(f)

        for i, data in tqdm(enumerate(st.session_state['data_dict'])):
            st.markdown(f"**Case**: {self.case}")
            st.markdown(f"**Previous Query**: {data['previous_query']}")
            st.markdown(data['tool_outputs'])
            st.markdown(data['llm_response'])
            total_count = data["manual_score"]["total_count"]
            total_score = data["manual_score"]["total_score"]
            st.number_input(
                "Number of correct entities",
                min_value=0,
                max_value=20,
                step=1,
                value=total_score,
                key=f"{i}_total_score",
                on_change=self.update_score,
                args=(i, "total_score")
            )

            st.number_input(
                "Number of entities",
                min_value=0,
                max_value=20,
                step=1,
                value=total_count,
                key=f"{i}_total_count",
                on_change=self.update_score,
                args=(i, "total_count")
            )

        if st.button('Submit'):
            with open(f'{self.case}/data_dict.json', 'w') as f:
                json.dump(st.session_state['data_dict'], f, indent=4)

    def llm_evaluate(self):
        df = pd.DataFrame(columns=['case', 'aspect', 'human_score', 'input_score'])
        # df_explain = pd.DataFrame(columns=['case', 'aspect', 'human_score', 'input_score', 'response'])

        for i, data in tqdm(enumerate(self.data_dict)):
            # Extract each pair of tool output and llm response
            tool_outputs = data['tool_outputs']
            llm_response = data['llm_response']
            data_type = data['type']
            previous_query = data['previous_query']
            current_entry = data['current_entry']

            for aspect in ['relevance', 'entailment', 'accessibility']:
                human_score = parse_current_entry(current_entry, aspect)
                if sum([1 for score in human_score if score != 'Not Applicable']) != 0:
                    response = self.evaluate_single_aspect(tool_outputs, llm_response, data_type, previous_query, aspect)
                    if response is not None:
                        input_score, reasonings = convert_scores(response, aspect)

                        assert len(human_score) == len(input_score)
                        print('input_score', len(input_score), 'reasoning', len(reasonings))
                        if len(human_score) == 1 and len(reasonings) > 1:
                            reasonings = reasonings[0]
                        # create a dataframe with one column for case name, one column for aspect, one for human score, and one for input score; append the dataframe df with the new data
                        if reasonings is not None and len(reasonings) > 0:
                            df = pd.concat([df, pd.DataFrame({
                                'case': [self.case] * len(human_score),
                                'aspect': [aspect] * len(human_score),
                                'human_score': human_score,
                                'input_score': input_score,
                                'reasoning': reasonings
                            })], ignore_index=True)
                        else:
                            df = pd.concat([df, pd.DataFrame({
                                'case': [self.case] * len(human_score),
                                'aspect': [aspect] * len(human_score),
                                'human_score': human_score,
                                'input_score': input_score,
                                'reasoning': [''] * len(human_score)
                            })], ignore_index=True)
                    else:
                        df = pd.concat([df, pd.DataFrame({
                            'case': [self.case] * len(human_score),
                            'aspect': [aspect] * len(human_score),
                            'human_score': human_score,
                            'input_score': [''] * len(human_score),
                            'reasoning': [''] * len(human_score)
                        })], ignore_index=True)

            for aspect in ['correctness']:
                response = self.evaluate_single_aspect(tool_outputs, llm_response, data_type, previous_query, aspect)
                try:
                    total_score, _, total_count, _, _ = convert_scores(response, aspect)
                except:
                    total_score, _, total_count, _, _ = convert_scores(response, aspect)

                data["auto_score"] = {"total_score": total_score, "total_count": total_count}
                data["manual_score"] = {"total_score": total_score, "total_count": total_count}

                if data_type == 'literature':
                    sbert_score = self.automatic_eval_for_literature(tool_outputs, llm_response)
                    data["auto_score"]["sbert_score"] = sbert_score

        # save the data_dict to a file
        with open(f'{self.case}/data_dict.json', 'w') as f:
            json.dump(self.data_dict, f, indent=4)

        df.to_csv(f'{self.case}/evaluation.csv', index=False)
        # df_explain.to_csv(f'{self.case}/evaluation_explain.csv', index=False)

    def automatic_eval_for_literature(self, tool_outputs, llm_response):
        sbert_score = score_sbert_similarity(tool_outputs, llm_response)
        return sbert_score


if __name__ == "__main__":
    print('Torch', torch.__version__)
    # Load hyperparameters
    try:
        with open('src/evaluation/config.yaml', 'r') as file:
            args = yaml.safe_load(file)
    except Exception as e:
        print('Error reading the config file')

    # Command-line argument parsing
    parser = argparse.ArgumentParser(description='Command line arguments')
    parser.add_argument('--model', type=str, default="gpt-4-turbo", help='Set LLM model. Choose from gpt-3.5-turbo, gpt-4-turbo, or gpt-4o')
    parser.add_argument('--case_folder', type=str, default=None, help='Set the case folder')
    parser.add_argument('--verbose', dest='verbose', action='store_true', help='Set verbose to True')
    cmd_args = parser.parse_args()

    # here is an example argument to run the evaluation script
    # Override args from config.yaml with command-line arguments if provided
    args['llm_model'] = cmd_args.model if cmd_args.model is not None else args['llm_model']
    args['case_folder'] = cmd_args.case_folder if cmd_args.case_folder is not None else args['case_folder']
    args['verbose'] = cmd_args.verbose if cmd_args.verbose is not None else args['verbose']

    # Initialize the evaluation class
    evaluator = Evaluator(args)
    evaluator.llm_evaluate()
    #evaluator.manual_evaluate()