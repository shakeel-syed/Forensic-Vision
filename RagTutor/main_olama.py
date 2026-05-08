from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 1 Create embedding model
text_data = text_data = [
    "The secret password is: BlueWhale99.",
    "The office lunch is pizza."
]

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2 Create chroma vector store (new API)
vectorstore = Chroma(
    collection_name="my_collection",
    embedding_function=embeddings
)


vectorstore.add_texts(text_data)

retriever = vectorstore.as_retriever()

# 3. Local LLM via Ollama
llm = ChatOllama(model="my-ollama-model")

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
