import sys
from pathlib import Path
import os
import django

# 1. Adiciona o diretório do projeto ao PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# 2. Configura Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ia_bot.settings")
django.setup()

# 3. Agora pode importar modelos e bibliotecas
from core.models import Parametro
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

# 4. Busca chave da OpenAI do banco
try:
    openai_key = Parametro.objects.get(parametroChave='OPENAI_API_KEY').parametroValor
except Parametro.DoesNotExist:
    raise EnvironmentError("Parâmetro OPENAI_API_KEY não encontrado no banco de dados.")

print(f"🔑 Chave OpenAI: {openai_key}")

# 5. Carrega arquivos
loader = DirectoryLoader(
    path="meus_arquivos",
    glob="**/*.txt",
    loader_cls=TextLoader,
    loader_kwargs={'encoding': 'utf-8'}
)
documents = loader.load()

# 6. Split
splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = splitter.split_documents(documents)

# 7. Embeddings + FAISS
embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
db = FAISS.from_documents(docs, embeddings)
db.save_local("vector_index")

print("✅ Índice FAISS criado e salvo com sucesso!")
