from html import parser
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.indexes import VectorstoreIndexCreator
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain.schema.runnable import RunnablePassthrough, RunnableLambda, RunnableParallel,RunnableBranch
# env loader
from dotenv import load_dotenv
load_dotenv()
# from langchain.vectorstores import Chroma
# from langchain.embeddings.ollama import OllamaEmbeddings
# from langchain.chains import SimpleChain

# Ensure you have the necessary environment variables set
openAi_model = ChatOpenAI(
    model = "gpt-3.5-turbo",
    temperature = 0.8,
)
mistralModel = ChatOllama(
    model = "mistral",
    temperature = 0.8,
)

voiceModel=ChatOllama(
    model = "sematre/orpheus:en",
    temperature = 0.8,
)

promt1=PromptTemplate(
    input_variables=["topic"],
    template="write a joke about: {topic}",
)

promt2=PromptTemplate(
    input_variables=["joke"],
    template="You are a helpful assistant. Provide a detailed explanation for: {joke}",
)


parser = StrOutputParser()

# # Create a chain that combines the prompt and the model
# class Person(BaseModel):

#     name: str = Field(description='Name of the person')
#     age: int = Field(gt=18, description='Age of the person')
#     city: str = Field(description='Name of the city the person belongs to')


# parser = PydanticOutputParser(pydantic_object=Person)

# template = PromptTemplate(
#     template='Generate the name, age and city of a fictional {place} person \n {format_instruction}',
#     input_variables=['place'],
#     partial_variables={'format_instruction':parser.get_format_instructions()}
# )

str_parser = StrOutputParser()
chain1 = promt1 | openAi_model | str_parser
chain2 = promt2 | openAi_model | str_parser

parallel_chain = RunnableParallel({
    'joke': RunnablePassthrough(),
    'explanation': chain2
})

final_chain = chain1 | parallel_chain

# print(final_chain.invoke({'topic':'cricket'})['joke'])

# print(final_chain.invoke({'topic':'cricket'})['explanation'])
# Get joke and explanation as before
# result = final_chain.invoke({'topic': 'cricket'})
# joke_text = result['joke']

# Use the voiceModel to generate audio from the joke text
audio_response = voiceModel.invoke('hlw! how are you?')  # Replace with the joke_text variable if needed

# Print or handle the audio response
print(audio_response)
