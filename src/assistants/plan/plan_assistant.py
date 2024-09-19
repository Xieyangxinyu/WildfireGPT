from src.assistants.assistant import Assistant
from src.config import client, model
import streamlit as st
from src.utils import stream_static_text, TEXT_CURSOR

class PlanAssistant(Assistant):
    def __init__(self, config_path, update_assistant, checklist):
        self.checklist = checklist
        super().__init__(config_path, update_assistant)
        self.function_dict = {
            "plan_complete": self.plan_complete,
        }
        self.init_message_sent = False
        
        '''
        self.feedback_assistant = client.beta.assistants.create(
                name="FeedbackAssistant",
                instructions= f"**Task**: Check the response carefully for correctness and give constructive criticism for how to improve it.\n\n\nThe plan assistant only has access to these datasets:\n{self.config['available_datasets']}.\n\n",
                model=model
            )
        '''

        stream_static_text(self.config['init_message'])
        st.session_state.messages.append({"role": "assistant", "content": self.config['init_message']})
    
    def initialize_instructions(self):
        return f"{self.config['instructions']}\n{self.config['available_datasets']}\n{self.config['example']}\nHere is the information about your client: {self.checklist}"
    
    def plan_complete(self, plan: str):
        args = {"checklist": self.checklist,
                "plan": plan}
        self.update_assistant("AnalystAssistant", args, new_thread = True)
        with open("chat_history/plan.txt", "w") as file:
            file.write(plan)
        return "Change Thread"
    
    
    def get_assistant_response(self, user_message=None, thread_id=None):
        stream_static_text(f"I'm working diligently to come up with a response for you... This may take a bit of time...🧐 Please do not respond yet ...{TEXT_CURSOR}")

        return super().get_assistant_response(user_message, thread_id)
    
    def respond_to_tool_output(self, thread_id, run_id, tool_outputs):
        if tool_outputs:
            if tool_outputs[0]['output'] == "Plan":
                tool_outputs[0]['output'] = self.config['dataset_decision'] + '\n' + self.checklist
                run = client.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread_id,
                    run_id=run_id,
                    tool_outputs=tool_outputs,
                )
                while run.status != 'completed':
                    pass
                if run.status == 'completed': 
                    messages = client.beta.threads.messages.list(
                        thread_id=thread_id
                    )
                    print(messages.data[0].content[0].text.value)
                full_response, _, _ = self.get_assistant_response(user_message="Explain to me what your plan is and ask me if I have any questions.", thread_id=thread_id)
            else:
                full_response = super().respond_to_tool_output(thread_id, run_id, tool_outputs)
        return full_response
