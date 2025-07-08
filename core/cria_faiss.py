from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import os

# Carregar chave da API do arquivo .env
from dotenv import load_dotenv
load_dotenv()
openai_key = os.getenv("OPENAI_API_KEY")

# 1. Carregar todos os arquivos .txt do diretório
loader = DirectoryLoader(
    path="meus_arquivos",             # pasta onde estão os arquivos
    glob="**/*.txt",                  # busca recursiva por arquivos .txt
    loader_cls=TextLoader,
    loader_kwargs={'encoding': 'utf-8'}
)

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

print("✅ Índice FAISS criado e salvo com sucesso com múltiplos arquivos!")
