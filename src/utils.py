from src.config import client, model
import yaml
import time
import streamlit as st
TEXT_CURSOR = "▕"

def load_config(path):
    """
    This function loads the config file.
    """
    with open(path, "r") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config

def get_assistant(config, initialize_instructions):
        """
        This function returns the assistant id from the config file.
        """
        name = config["name"]
        instructions = initialize_instructions()
        tools = populate_tools(config)
        if tools:
            assistant = client.beta.assistants.create(
                name=name,
                instructions=instructions,
                tools=tools,
                model=model,
                top_p=0.8,
                temperature=0.7,
            )
        else:
            assistant = client.beta.assistants.create(
                name=name,
                instructions=instructions,
                model=model,
                top_p=0.8,
                temperature=0.7,
            )
        #with open(f"{config['path']}", "w") as f:
        #    yaml.dump(config, f)
        return assistant

def populate_tools(config):
    """
    This function populates the tools dictionary with the functions
    defined in the config file.
    """
    tools = []
    if "available_functions" not in config.keys():
        return None
    for tool_name, tool_meta_data in config["available_functions"].items():
        tool = {}
        tool["type"] = "function"
        tool["function"] = {}
        tool["function"]["name"] = tool_name
        tool["function"]["description"] = tool_meta_data["description"]
        tool["function"]["parameters"] = {}
        tool["function"]["parameters"]["type"] = "object"
        tool["function"]["parameters"]["properties"] = {}
        if tool_meta_data["parameters"]:
            for param_name, param_meta_data in tool_meta_data["parameters"].items():
                param = {}
                param["type"] = param_meta_data["type"]
                param["description"] = param_meta_data["description"]
                tool["function"]["parameters"]["properties"][param_name] = param
        tool["function"]["parameters"]["required"] = tool_meta_data["required"]
        tools.append(tool)
    return tools

def create_thread():
    thread = client.beta.threads.create()
    return thread

def add_appendix(response: str, appendix_path: str):
    """
    This function adds the examples to the response.
    
    Args:
        response (str): The response string.
        appendix_path (str): The path to the appendix markdown file.
    """
    with open(appendix_path, "r") as f:
        appendix = f.read()
    response += appendix
    return response

def get_openai_response(messages, top_p = 0.95, max_tokens = 256, temperature = 0.7):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        top_p=top_p,
        max_tokens=max_tokens,
        temperature=temperature
    )
        
    return response.choices[0].message.content

def create_text_stream(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.08)

def stream_static_text(text):
    stream_text = create_text_stream(text)
    st.write_stream(stream_text)


def get_conversation_summary(messages, summary_instructions = "**Please summarize the previous conversation in a few sentences.**", max_tokens = 512):
    """
    This function returns a summary of the conversation by calling the OpenAI API.
    """

    messages += [{"role": "system", "content": summary_instructions}]

    response = get_openai_response(messages, max_tokens=max_tokens)

    return response



def retry_on_generation_error(messages, response, possible_actions, exact_match = False):
    """
    This function retries the generation if the response is not in the list of possible actions.
    """
    if exact_match:
        while response not in possible_actions:
            response = get_openai_response(messages, temperature = 1)
    else:
        while not any([action in response for action in possible_actions]):
            response = get_openai_response(messages, temperature = 1)
    return response


def get_openai_response_with_retries(messages, possible_actions, top_p = 0.95, max_tokens = 256, temperature = 0.7, exact_match = False):
    response = get_openai_response(messages, top_p = top_p, max_tokens = max_tokens, temperature = temperature)
    return retry_on_generation_error(messages, response, possible_actions, exact_match = exact_match)



