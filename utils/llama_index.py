import os

# This is not used but required by llama-index and must be imported FIRST
os.environ["OPENAI_API_KEY"] = "sk-abc123"

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.memory import ChatMemoryBuffer

###################################
#
# Create Chat Memory
#
###################################

def create_chat_memory(token_limit: int = 2500):
    memory = ChatMemoryBuffer.from_defaults(token_limit=token_limit)
    return memory

###################################
#
# Create Data Index
#
###################################

def create_data_index():
    try:
        data_dir = os.getcwd() + "/data"
        data = SimpleDirectoryReader(input_dir=data_dir).load_data()
        index = VectorStoreIndex.from_documents(data)
        print(type(index))
        return index
    except Exception as err:
        print(f"Error creating data index: {err}")
        return index == None