from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os

# Carregar chave da API
from dotenv import load_dotenv
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")

# 1. Carregar os arquivos ou textos
loader = TextLoader("meu_arquivo.txt", encoding="utf-8")  # ou use PDFLoader, etc.
documents = loader.load()

# 2. Quebrar em partes menores (chunks)
splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = splitter.split_documents(documents)

# 3. Gerar embeddings
embeddings = OpenAIEmbeddings(openai_api_key=openai_key)

# 4. Criar o índice FAISS
db = FAISS.from_documents(docs, embeddings)

# 5. Salvar o índice em disco
db.save_local("vector_index")

print("Índice FAISS criado e salvo com sucesso!")
