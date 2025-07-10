import json
import os
from pathlib import Path
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
from django.shortcuts import render, get_object_or_404, redirect
from .models import Parametro
from .forms import ParametroForm

try:
    openai_key = Parametro.objects.get(parametroChave='OPENAI_API_KEY').parametroValor
except Parametro.DoesNotExist:
    raise EnvironmentError("Parâmetro OPENAI_API_KEY não encontrado no banco de dados.")

# Verificação opcional
print(f"Chave OpenAI do bancohhhh: {openai_key}")

embeddings = OpenAIEmbeddings(openai_api_key=openai_key)


class EmbeddingView(APIView):
    def get(self, request):
        result = embeddings.embed_query("Olá, mundo!")
        return Response({"embedding": result})


@csrf_exempt
def responder_pergunta(request):
    print("Iniciando responder_pergunta...")
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
            "Formate o texto com quebras de linha e parágrafos, se necessário."
        )

        try:
            openai_key = Parametro.objects.get(parametroChave='OPENAI_API_KEY').parametroValor
            print(f"Chave OpenAI: {openai_key}")
        except Parametro.DoesNotExist:
            raise EnvironmentError("Parâmetro OPENAI_API_KEY não encontrado no banco de dados.")
        #client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print(f"Chave OpenAI2: {openai_key}")
        client = OpenAI(api_key=openai_key)
        print(client)
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
        print("Recebendo mensagem do usuário...")
        texto_usuario = request.POST.get('mensagem')
        if texto_usuario:
            # Salva a mensagem do usuário
            Mensagem.objects.create(texto=texto_usuario, enviado_por_usuario=True)

            # Checa se é a primeira vez (sem mensagens no banco)
            #print(Mensagem.objects.count())
            if Mensagem.objects.count() == 1:
                Mensagem.objects.create(texto="Olá, sou a Vivi da Vila 11. Seja muito bem vindo(a).", enviado_por_usuario=False)
                Mensagem.objects.create(texto="🔒 Ao prosseguir, você estará de acordo com os nossos Termos de Uso e nossa Política de Privacidade.", enviado_por_usuario=False)
                Mensagem.objects.create(texto="Garantimos que seus dados estão seguros e sendo utilizados apenas para fins relacionados ao atendimento.", enviado_por_usuario=False)
                Mensagem.objects.create(texto="Para mais detalhes, acesse: https://vila11.com.br/politica-de-privacidade/", enviado_por_usuario=False)
                Mensagem.objects.create(texto="Para seguirmos com seu cadastro em nosso sistema, por favor, poderia me falar seu nome e sobrenome?", enviado_por_usuario=False)
            elif Mensagem.objects.count() == 7:
                Mensagem.objects.create(texto="E qual é o seu e-mail para que possamos continuar?", enviado_por_usuario=False)
            elif Mensagem.objects.count() == 9:
                Mensagem.objects.create(texto="Perfeito! Agora, como posso te ajudar hoje?", enviado_por_usuario=False)
            else:
                #print("Processando mensagem do usuário...")
                try:
                    # Verifica índice FAISS
                    print("Verificando índice FAISS...")
                    vector_dir = "vector_index"
                    if not os.path.exists(os.path.join(vector_dir, "index.faiss")):
                        resposta_texto = "Erro: índice de conhecimento não encontrado."
                    else:
                        # Carrega embeddings e índice FAISS
                        print("Carregando embeddings e índice FAISS...")
                        embeddings = OpenAIEmbeddings()
                        db = FAISS.load_local(
                            vector_dir,
                            embeddings,
                            allow_dangerous_deserialization=True
                        )
                        print("Índice FAISS carregado com sucesso.")

                        # Chamada à OpenAI
                        try:
                            openai_key = Parametro.objects.get(parametroChave='OPENAI_API_KEY').parametroValor
                            print(f"Chave OpenAI do banco: {openai_key}")
                        except Parametro.DoesNotExist:
                            raise EnvironmentError("Parâmetro OPENAI_API_KEY não encontrado no banco de dados.")
                        
                        # Busca contexto
                        print("Buscando contexto relevante...")
                        print(f"Texto do usuário: {texto_usuario}")
                        docs = db.similarity_search(texto_usuario, k=3)
                        print(f"Documentos encontrados: {len(docs)}")
                        contexto = "\n\n".join([doc.page_content for doc in docs])
                        print(f"Contexto encontrado com sucesso.: {contexto}")
                        # Prompt
                        system_prompt = (
                            "Você é um atendente da empresa Vila11 e responde perguntas sobre contratos, aluguéis e documentos. "
                            "Responda com base apenas no conteúdo abaixo. Se não houver informação suficiente, diga que não é possível responder com precisão."
                            "Formate o texto com quebras de linha e parágrafos, se necessário."
                        )
                        print(system_prompt)

                        print(f"Chave OpenAI: {openai_key}")
                        client = OpenAI(api_key=openai_key)

                        print("Gerando resposta com OpenAI...")
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": f"Contexto:\n{contexto}"},
                                {"role": "user", "content": texto_usuario}
                            ]
                        )
                        resposta_texto = response.choices[0].message.content
                        print(f"Resposta gerada com sucesso.: {resposta_texto}")

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

@csrf_exempt
def parametro_list(request):
    parametros = Parametro.objects.all().values('id', 'parametroChave', 'parametroValor')  # ou fields conforme seu modelo
    return JsonResponse(list(parametros), safe=False)

@csrf_exempt
def parametro_create(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

        form = ParametroForm(data)
        if form.is_valid():
            parametro = form.save()
            return JsonResponse({
                'id': parametro.id,
                'parametroChave': parametro.parametroChave,
                'parametroValor': parametro.parametroValor,
                'mensagem': 'Parâmetro criado com sucesso!'
            }, status=201)
        else:
            return JsonResponse({'errors': form.errors}, status=400)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

@csrf_exempt
def parametro_update(request, pk):
    parametro = get_object_or_404(Parametro, pk=pk)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

        form = ParametroForm(data, instance=parametro)
        if form.is_valid():
            parametro = form.save()
            return JsonResponse({
                'success': True,
                'parametro': {
                    'id': parametro.id,
                    'chave': parametro.parametroChave,
                    'valor': parametro.parametroValor
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    else:
        return JsonResponse({
            'id': parametro.id,
            'chave': parametro.parametroChave,
            'valor': parametro.parametroValor
        })

@csrf_exempt
def parametro_delete(request, pk):
    parametro = get_object_or_404(Parametro, pk=pk)

    if request.method == 'POST':
        parametro.delete()
        return JsonResponse({
            'success': True,
            'message': f"Parâmetro '{parametro.parametroChave}' excluído com sucesso."
        })

    # Para requisição GET, apenas retorna os dados do parâmetro
    return JsonResponse({
        'id': parametro.id,
        'chave': parametro.parametroChave,
        'valor': parametro.parametroValor
    })
