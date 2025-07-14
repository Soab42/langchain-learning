from langchain.prompts import PromptTemplate
from langchain_core.output_parsers.pydantic import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

# --- Pydantic Model for Greeting/Reply Output ---
class GreetingOutput(BaseModel):
    subject: str = Field(description="Subject line for the email")
    email: str = Field(description="Full email greeting message in plain text")
    sms: str = Field(description="Short SMS greeting message under 160 characters")
    html_card: str = Field(description="HTML card version of the greeting for email")

greeting_parser = PydanticOutputParser(pydantic_object=GreetingOutput)

# --- Prompt Template for Greetings ---
greeting_prompt = PromptTemplate(
    input_variables=["name", "occasion", "format_instructions"],
    template="""
    Create a professional and friendly {occasion} greeting for {name} suitable for sending via email and SMS.

    - Generate a subject line for the email.
    - Write a full email greeting message in plain text.
    - Write a short SMS greeting message (under 160 characters).
    - Write an HTML card version of the greeting (with a nice layout, suitable for email, using inline CSS, and including the sender "sam haque, commartial landers ltd! 123 Main Street New York, NY 10001 USA" at the bottom).
    {format_instructions}
    Ensure the output is strict JSON (no trailing commas, use double quotes, no comments).
    """
)

# --- LLM Chain for Greetings ---
def get_greeting_chain(llm):
    return greeting_prompt.partial(format_instructions=greeting_parser.get_format_instructions()) | llm | greeting_parser

# --- General AI Reply (for auto-reply) ---
def generate_ai_reply(llm, subject, body):
    prompt = f"You are an AI assistant. Read the email below and generate a professional reply.\n\nSubject: {subject}\n\nBody:\n{body}"
    return llm.invoke(prompt)

# --- Example LLM loader ---
def get_llm():
    # Customize with your OpenAI API key as needed
    return ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)