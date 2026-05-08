import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# Set your API key
os.environ["GOOGLE_API_KEY"] = "AIzaSyBg45dSMf0ur3bC0CSlay2hGtl3w7RXgP8"

# 1. Create Google embedding model
text_data = [
    "The secret password is: BlueWhale99.",
    "The office lunch is pizza."
]

# Use Google's embedding model
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# 2. Create chroma vector store
vectorstore = Chroma(
    collection_name="my_collection",
    embedding_function=embeddings
)
vectorstore.add_texts(text_data)
retriever = vectorstore.as_retriever()

# 3. Gemini LLM
# Use "gemini-2.5-flash"
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# 4. RAG chain
template = "Answer based on context: {context}\nQuestion: {question}"

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}

    | ChatPromptTemplate.from_template(template)
    | llm
    | StrOutputParser()
)

print(rag_chain.invoke("What is the secret password?"))
print(rag_chain.invoke("What is the office lunch?"))
