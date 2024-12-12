from abc import ABC

import dotenv
import streamlit as st
from langchain.chat_models import ChatOpenAI
from langchain.schema import ChatMessage
from langchain.schema.callbacks.base import BaseCallbackHandler

from llm_helpers.ChatMemory import ChatMemory
from tools.ToolManager import ToolManager

dotenv.load_dotenv()
config = dotenv.dotenv_values()

# Basic designing features
st.title("WQU")
st.title("M.Sc. Financial Engineering")
st.title("Capstone Project")

st.divider()

st.header("Financial RAG Agent - Chat Interface")

# Session storage for Streamlit
ss = st.session_state


# Stream handler for showing the conversation
class StreamHandler(BaseCallbackHandler, ABC):
    """Handles the streaming of messages from the LLM model to the chat."""

    def __init__(self, container: st.container, initial_text=""):
        self.container = container
        self.text = initial_text

    def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Callback when a new token is generated by the LLM."""
        self.text += token
        last_piece = self.text.split("\n")[-1]
        if len(last_piece) > 60:
            self.text += "\n"
        self.container.text(self.text)


# Tool manager, chat agent, and conversational memory
tm = ToolManager()
chat_agent = tm.chat_agent
memory = ChatMemory()
ss["config_messages"] = [memory.context[0], memory.context[1]]

# Show the welcome message, but not the system prompt
for msg in st.session_state.config_messages:
    if msg.role != "system":
        st.chat_message(msg.role).write(msg.content)

# User prompt and chatbot response handling
if prompt := st.chat_input():

    # Definition of the user messages and adding to the memory
    st.chat_message("user").write(prompt)
    memory.add("user", prompt)
    ss["config_messages"].append(ChatMessage(role="user", content=prompt))

    with st.chat_message("assistant"):
        stream_handler = StreamHandler(st.empty())
        with st.spinner("Started Investigation..."):

            # Generate assistant response and stream it to front-end
            with st.spinner("Consulting Helper Agent..."):
                helper_agent_response = chat_agent.run(str(memory.context))
            helper_agent_response = str(helper_agent_response)
            st.success("Helper Agent Consultation is complete.")
            with st.expander("Helper Agent Response", expanded=False):
                st.warning("\n\n" + helper_agent_response + "\n\n")

            with st.spinner("Instantiating the Main Agent for Processing Information..."):
                main_agent = ChatOpenAI(openai_api_key=config["OPENAI_API_KEY"],
                                        streaming=True,
                                        model_name="gpt-3.5-turbo",
                                        callbacks=[stream_handler])
            st.success("Main Agent Instantiation is complete.")

            with st.spinner("Main Agent is analyzing the information..."):
                main_agent_response = main_agent([
                    memory.context[0],  # System Prompt
                    memory.context[1],  # Assistant Welcome Message
                    memory.context[2],  # User Question
                    ChatMessage(role="system", content=helper_agent_response,
                                handle_parsing_errors=True)  # Helper Agent Response
                ])
            st.success("Main Agent Analysis is complete.")

            if "sorry" in main_agent_response.content.lower() or \
                    "apologize" in main_agent_response.content.lower() or \
                    "apologies" in main_agent_response.content.lower():
                st.error("Failure in processing the information.")
            else:
                st.success("Investigation is complete.")

            memory.add("assistant", main_agent_response.content)
            ss["config_messages"].append(main_agent_response)
