import json
import os
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from .models import Mensagem
from openai import OpenAI
from django.shortcuts import redirect


load_dotenv()  # Carrega variáveis do .env

# Instancia embeddings uma única vez
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise EnvironmentError("OPENAI_API_KEY não está definido no ambiente ou .env")

embeddings = OpenAIEmbeddings(openai_api_key=openai_key)


class EmbeddingView(APIView):
    def get(self, request):
        result = embeddings.embed_query("Olá, mundo!")
        return Response({"embedding": result})


@csrf_exempt
def responder_pergunta(request):
    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido"}, status=405)

    try:
        if not request.body:
            return JsonResponse({"erro": "Corpo da requisição vazio."}, status=400)

        data = json.loads(request.body)
        pergunta = data.get("input", {}).get("text", "").strip()

        if not pergunta:
            return JsonResponse({"erro": "Pergunta vazia"}, status=400)

        vector_dir = "vector_index"
        if not os.path.exists(os.path.join(vector_dir, "index.faiss")):
            return JsonResponse({"erro": "Índice FAISS não encontrado"}, status=500)

        embeddings = OpenAIEmbeddings()
        db = FAISS.load_local(
            vector_dir,
            embeddings,
            allow_dangerous_deserialization=True
        )

        docs = db.similarity_search(pergunta, k=3)
        contexto = "\n\n".join([doc.page_content for doc in docs])

        system_prompt = (
            "Você é um atendente da empresa Vila11 e responde perguntas sobre contratos, aluguéis e documentos. "
            "Responda com base apenas no conteúdo abaixo. Se não houver informação suficiente, diga que não é possível responder com precisão."
        )

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Contexto:\n{contexto}"},
                {"role": "user", "content": pergunta}
            ]
        )

        resposta_texto = response.choices[0].message.content

        return JsonResponse({
            "replies": [{"type": "text/plain", "value": resposta_texto}]
        })

    except json.JSONDecodeError:
        return JsonResponse({"erro": "JSON inválido"}, status=400)

    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)
    

def chatbot(request):
    if request.method == 'POST':
        texto_usuario = request.POST.get('mensagem')
        if texto_usuario:
            # Salva a mensagem do usuário
            Mensagem.objects.create(texto=texto_usuario, enviado_por_usuario=True)

            try:
                # Verifica índice FAISS
                vector_dir = "vector_index"
                if not os.path.exists(os.path.join(vector_dir, "index.faiss")):
                    resposta_texto = "Erro: índice de conhecimento não encontrado."
                else:
                    # Carrega embeddings e índice FAISS
                    embeddings = OpenAIEmbeddings()
                    db = FAISS.load_local(
                        vector_dir,
                        embeddings,
                        allow_dangerous_deserialization=True
                    )

                    # Busca contexto
                    docs = db.similarity_search(texto_usuario, k=3)
                    contexto = "\n\n".join([doc.page_content for doc in docs])

                    # Prompt
                    system_prompt = (
                        "Você é um atendente da empresa Vila11 e responde perguntas sobre contratos, aluguéis e documentos. "
                        "Responda com base apenas no conteúdo abaixo. Se não houver informação suficiente, diga que não é possível responder com precisão."
                    )

                    # Chamada à OpenAI (nova API)
                    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Contexto:\n{contexto}"},
                            {"role": "user", "content": texto_usuario}
                        ]
                    )
                    resposta_texto = response.choices[0].message.content

            except Exception as e:
                resposta_texto = f"Erro ao gerar resposta: {str(e)}"

            # Salva resposta do bot
            Mensagem.objects.create(texto=resposta_texto, enviado_por_usuario=False)

    mensagens = Mensagem.objects.order_by('timestamp')
    return render(request, 'chat/chatbot.html', {'mensagens': mensagens})

@csrf_exempt
def limpar_historico(request):
    if request.method == 'POST':
        Mensagem.objects.all().delete()
    return redirect('chatbot')