from src.assistants.assistant import Assistant
from src.assistants.analyst.FWI import FWI_retrieval
from src.assistants.analyst.history import long_term_fire_history_records
from src.assistants.analyst.incident import recent_fire_incident_data
from src.assistants.analyst.literature import literature_search
from src.assistants.analyst.census import get_census_info
from src.assistants.analyst.utils import display_maps, display_plots
from src.config import client
import streamlit as st
from src.utils import get_openai_response_with_retries, stream_static_text, get_conversation_summary, TEXT_CURSOR
import time


class AnalystAssistant(Assistant):
    def __init__(self, config_path, update_assistant, checklist, plan):
        self.checklist = checklist
        self.plan = plan
        super().__init__(config_path, update_assistant)
        self.function_dict = {
            "long_term_fire_history_records": long_term_fire_history_records,
            "recent_fire_incident_data": recent_fire_incident_data,
            "fire_weather_index": FWI_retrieval,
            "literature_search": literature_search,
            "census": get_census_info
        }

        stream_static_text(self.config['init_message'])
        st.session_state.messages.append({"role": "assistant", "content": self.config['init_message']})

    def initialize_instructions(self):
        return self.config["instructions"] + "\n" + self.checklist + "\nHere is your plan to assist your clinet:\n" + self.plan
    
    def get_summary(self, thread_id):
        thread_messages = client.beta.threads.messages.list(thread_id).data
        thread_messages = thread_messages[::-1]
        roles = [message.role for message in thread_messages]
        thread_messages = [message.content[0].text.value for message in thread_messages]
        summary = get_conversation_summary([{"role": role, "content": content} for role, content in zip(roles, thread_messages)])
        return summary


    def get_follow_up(self, summary, addtional_message, possible_actions=None, user_message=None, temperature=0.7, max_tokens=50, exact_match=False):

        if user_message:
            system_message = f"Here is your overall plan to assist your client:\n{self.plan}\n\nHere is the summary of the conversation so far:\n{summary}\n\nHere is the most recent message from the client:\n{user_message}"
        else:
            system_message = f"Here is your overall plan to assist your client:\n{self.plan}\n\nHere is the summary of the conversation so far:\n{summary}\n\n"
        
        messages = [{"role": "system", "content": system_message}] + addtional_message

        # print(f"follow_up_system_message: {system_message}")

        follow_up = get_openai_response_with_retries(messages, possible_actions, temperature=temperature, max_tokens=max_tokens, exact_match=exact_match)
        
        return follow_up
        

    def decision_point(self, thread_id, user_message = None):
        summary = self.get_summary(thread_id)
        follow_up = None
        thread_messages = client.beta.threads.messages.list(thread_id).data

        if len(thread_messages) > 0 and thread_messages[0].role == "user":
            user_message = thread_messages[0].content[0].text.value
        if user_message:
            addtional_message = [{"role": "system", "content": self.config['query_assessment_instructions']}]
            follow_up = self.get_follow_up(summary, addtional_message, possible_actions=["Respond to the client's questions.", "Proceed with the plan."],
                                           user_message = user_message, exact_match=True)

        if follow_up:
            addtional_message = [{"role": "system", "content": f"You have decided do the following: {follow_up}. {self.config['tiny_plan_instructions']}"}]
        else:
            addtional_message = [{"role": "system", "content": self.config['tiny_plan_instructions']}]

        possible_tools = ["fire_weather_index", "long_term_fire_history_records", "recent_fire_incident_data", "literature_search", "census", "no tool needed"]

        available_tools = self.get_follow_up(summary, addtional_message, possible_actions = possible_tools, user_message = user_message)
        
        if follow_up:
            follow_up += " " + available_tools
        else:
            follow_up = available_tools

        if "no tool needed" in available_tools:
            stream_static_text(self.config['caution_message'])
            time.sleep(1)
        
        print(f"follow_up_message: {follow_up}")
        return follow_up
    
    def get_assistant_response(self, user_message=None, thread_id = None):
        stream_static_text(f"I'm working diligently on my analysis for you... This may take a bit of time...🧐 Please do not respond yet ...{TEXT_CURSOR}")
        
        if user_message is not None:
            _ = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_message
            )
            self.visualizations = []

        message = self.decision_point(thread_id, user_message)

        if not user_message:
            instructions = f"Here is the information about your client:\n\n{self.checklist}\n\nHere is your overall plan to assist your client: {self.plan}\n\nHere is your plan for this step: {message}\n\nIf you give any recommendations, please provide the reasoning behind them and suggest the client to ask for supporting scientific evidence."
        else:
            instructions = f"Here is the information about your client:\n\n{self.checklist}\n\nHere is your overall plan to assist your client: {self.plan}\n\nHere is your client's last message: {user_message}\n\nHere is your plan for this step: {message}\n\nIf you give any recommendations, please provide the reasoning behind them and suggest the client to ask for supporting scientific evidence."
        
        stream = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id,
            stream=True,
            instructions=instructions,
            parallel_tool_calls=False
        )
        full_response, run_id, tool_outputs = self.stream_output(stream)

        return full_response, run_id, tool_outputs
    
    def add_appendix(self, function_response, function_name):
        config = self.config
        if config["available_functions"][function_name]["appendix"]:
            path = config["path"] + "appendix/" + config["available_functions"][function_name]["appendix"]
            with open(path, "r") as f:
                appendix = f.read()
            function_response += appendix
        return function_response
    

    def on_tool_call_created(self, tool):
        response = super().on_tool_call_created(tool)
        if type(response) != str:
            response, maps, figs = response
            display_maps(maps)
            display_plots(figs)
            if maps is not None or len(figs) > 0:
                self.visualizations.append([maps, figs])
        response = self.add_appendix(response, tool.function.name)
        return response
