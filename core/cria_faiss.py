import sys
from pathlib import Path
import os
import django

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ia_bot.settings")
django.setup()

from core.models import Parametro
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader, CSVLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

try:
    openai_key = Parametro.objects.get(parametroChave='OPENAI_API_KEY').parametroValor
except Parametro.DoesNotExist:
    raise EnvironmentError("Parâmetro OPENAI_API_KEY não encontrado no banco de dados.")

print(f"🔑 Chave OpenAI: {openai_key}")

# Carregar arquivos .txt
loader_txt = DirectoryLoader(
    path="meus_arquivos",
    glob="**/*.txt",
    loader_cls=TextLoader,
    loader_kwargs={'encoding': 'utf-8'}
)
docs_txt = loader_txt.load()

loader_csv = DirectoryLoader(
    path="meus_arquivos",
    glob="**/*.csv",
    loader_cls=CSVLoader,
    loader_kwargs={"encoding": "utf-8"}
)
docs_csv = loader_csv.load()

documents = docs_txt + docs_csv

splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = splitter.split_documents(documents)

embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
db = FAISS.from_documents(docs, embeddings)
db.save_local("vector_index")

print("✅ Índice FAISS criado e salvo com sucesso!")
