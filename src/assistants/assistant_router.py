from src.assistants.profile import ChecklistAssistant
from src.assistants.plan import PlanAssistant
from src.assistants.analyst import AnalystAssistant
from src.config import client

class AssistantRouter:
    def __init__(self, name, thread_id = None, args={}):
        if thread_id:
            self.current_thread = client.beta.threads.retrieve(thread_id)
            self.new_thread = False
        else:
            self.current_thread = client.beta.threads.create()
            self.new_thread = True
        # append the thread id in `chat_history/threads.txt`
        with open("chat_history/threads.txt", "a") as f:
            f.write(f"{self.current_thread.id}\n")
        
        self.assistant_dict = {
            "ChecklistAssistant": [ChecklistAssistant, "src/assistants/profile/config.yml"],
            "FollowUpAssistant": [ChecklistAssistant, "src/assistants/profile/config_follow_up.yml"],
            "PlanAssistant": [PlanAssistant, "src/assistants/plan/config.yml"],
            "AnalystAssistant": [AnalystAssistant, "src/assistants/analyst/config.yml"]
        }

        Assistant = self.assistant_dict[name][0]
        config_path = self.assistant_dict[name][1]
        self.current_assistant = Assistant(config_path, self.update_assistant, **args)

        if False:
            '''This is a short cut to plan assistant; for testing purposes'''
            checklist = '- Profession: Risk Manager\n- Concern: High intensity fire near Las Vegas, NM; primary risk factors to be concerned about.\n- Location: Sangre de Cristo Mountains \n- Time: Immediate measures to mitigate risks\n- Scope: Water resources and unpaved roads\n'
            args = {"checklist": checklist}
            self.update_assistant("PlanAssistant", args, new_thread = True)
    
    def update_assistant(self, name, args, new_thread = False):
        Assistant = self.assistant_dict[name][0]
        config_path = self.assistant_dict[name][1]
        self.current_assistant = Assistant(config_path, self.update_assistant, **args)
        if new_thread:
            self.current_thread = client.beta.threads.create()
            with open("chat_history/threads.txt", "a") as f:
                f.write(f"{self.current_thread.id}\n")
            self.new_thread = True

    def get_assistant_response(self, user_message: str = None):
        self.new_thread = False
        full_response, run_id, tool_outputs = self.current_assistant.get_assistant_response(user_message, self.current_thread.id)
        if len(tool_outputs):
            full_response += "\n\n"
            full_response += self.current_assistant.respond_to_tool_output(self.current_thread.id, run_id, tool_outputs)
        elif self.new_thread:
            return self.get_assistant_response()
        if len(self.current_assistant.visualizations) > 0:
            full_response = [full_response, self.current_assistant.visualizations]
            self.current_assistant.visualizations = []
        return full_response
    
    def resume_conversation(self):
        current_thread = self.current_thread
        thread_messages = client.beta.threads.messages.list(current_thread.id).data

        while len(thread_messages) > 1 and thread_messages[0].role != 'user':
            thread_messages = thread_messages[1:]
        thread = client.beta.threads.create()
        for message in thread_messages[::-1]:
            role = message.role
            content = message.content[0].text.value
            client.beta.threads.messages.create(
                thread.id,
                role=role,
                content=content,
            )
        self.current_thread = thread
        self.new_thread = False
        #client.beta.threads.delete(current_thread.id)
        with open("chat_history/threads.txt", "a") as f:
            f.write(f"{self.current_thread.id}\n")

            
