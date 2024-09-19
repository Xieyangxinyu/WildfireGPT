from src.utils import get_assistant, create_thread, load_config
from src.config import client
from src.assistants.stream import check_tool_call, manage_tool_call, check_message_delta, get_text_stream, get_text_delta
import json
import streamlit as st
from abc import ABC, abstractmethod
from src.utils import TEXT_CURSOR

class Assistant(ABC):
    def __init__(self, config_path, update_assistant):
        self.config = load_config(config_path)
        self.function_dict = {}
        self.update_assistant = update_assistant
        self.assistant = get_assistant(self.config, self.initialize_instructions)
        self.assistant.id = self.assistant.id
        self.visualizations = []
    
    @abstractmethod
    def initialize_instructions(self):
        pass
    
    def stream_output(self, stream):
        tool_outputs = []
        full_response = ''
        streaming = False
        message_placeholder = st.empty()
        for event in stream:
            if check_tool_call(event):
                tool_outputs += manage_tool_call(event, self.on_tool_call_created)
            if check_message_delta(event):
                text_stream = get_text_stream(event)
                if not streaming:
                    streaming = True
                    message_placeholder.empty()
                for delta in text_stream:
                    text_delta = get_text_delta(delta)
                    full_response += (text_delta or "")
                    message_placeholder.markdown(full_response + TEXT_CURSOR)
        run_id = event.data.id
        return full_response, run_id, tool_outputs
    

    def add_assistant_message(self, message, thread_id):
        _ = client.beta.threads.messages.create(
            thread_id=thread_id,
            role="assistant",
            content=message
        )

    
    def get_assistant_response(self, user_message=None, thread_id = None):
        if thread_id == None:
            thread = create_thread()
            thread_id = thread.id
        
        if user_message:
            _ = client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=user_message
            )

        stream = client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id,
            stream=True,
            parallel_tool_calls=False
        )

        full_response, run_id, tool_outputs = self.stream_output(stream)
        #print(f"full_response: {full_response}")
        return full_response, run_id, tool_outputs
    
    def respond_to_tool_output(self, thread_id, run_id, tool_outputs):
        if tool_outputs:

            stream = client.beta.threads.runs.submit_tool_outputs(
                thread_id=thread_id,
                run_id=run_id,
                tool_outputs=tool_outputs,
                stream=True,
            )
            full_response, _, _ = self.stream_output(stream)

            with open("chat_history/tools.txt", "a") as f:
                f.write("\n\n\n\n**Tool Outputs**\n")
                for tool_output in tool_outputs:
                    f.write(tool_output['output'])
                f.write("\n**LLM Response**\n")
                f.write(full_response)
                f.write("\n")
        return full_response

    def on_tool_call_created(self, tool):
        function = self.function_dict.get(tool.function.name)
        function_args = json.loads(tool.function.arguments)
        response = function(**function_args)
        return response
