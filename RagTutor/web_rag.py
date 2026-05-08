import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from dotenv import load_dotenv
load_dotenv() # Load from .env file

# API key will now be read from os.environ["GOOGLE_API_KEY"] automatically by LangChain

# 1. Fetch content from the URL
loader = WebBaseLoader("https://dsmasjid.com/")
docs = loader.load()

# Split the content into smaller chunks
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
splits = text_splitter.split_documents(docs)

# Use Google's embedding model
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

# 2. Create chroma vector store
vectorstore = Chroma.from_documents(
    documents=splits,
    embedding=embeddings,
    collection_name="web_collection"
)
retriever = vectorstore.as_retriever()

# 3. Gemini LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# 4. RAG chain
template = """Answer based on context:
{context}

Question: {question}"""

rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | ChatPromptTemplate.from_template(template)
    | llm
    | StrOutputParser()
)

# 5. Interactive loop
print("Web RAG initialized for https://dsmasjid.com/")
while True:
    user_question = input("\nEnter your question (or 'exit' to quit): ")
    if user_question.lower() in ['exit', 'quit']:
        break
    
    if user_question.strip():
        response = rag_chain.invoke(user_question)
        print("\nAnswer:", response)
