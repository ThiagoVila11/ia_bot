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
from .forms import ParametroForm, MensagemForm, ContextoForm


def get_openai_key():
    try:
        key = Parametro.objects.get(parametroChave='OPENAI_API_KEY').parametroValor.strip()
        if not key or not key.startswith("sk-"):
            raise ValueError("Chave OpenAI inválida ou ausente.")
        return key
    except Parametro.DoesNotExist:
        raise EnvironmentError("Parâmetro OPENAI_API_KEY não encontrado no banco de dados.")


# Busca chave uma vez no início para os embeddings usados globalmente
openai_key = get_openai_key()
print(f"🔑 Chave OpenAI: {openai_key}")
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

        openai_key = get_openai_key()
        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
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
            "Responda de forma clara e objetiva, evitando jargões técnicos desnecessários."
        )

        openai_key = get_openai_key()
        print(f"Chave OpenAI usada: {openai_key}")
        client = OpenAI(api_key=openai_key)

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
    if not request.session.session_key:
        request.session.save()  # garante que a sessão seja criada

    session_id = request.session.session_key
    #print(f"ID da sessão: {session_id}")
    if request.method == 'POST':
        #print("Recebendo mensagem do usuário...")
        texto_usuario = request.POST.get('mensagem')
        if texto_usuario:
            # Salva a mensagem do usuário
            #Mensagem.objects.create(texto=texto_usuario, enviado_por_usuario=True)
            Mensagem.objects.create(session_id=session_id, texto=texto_usuario, enviado_por_usuario=True)
            user_messages = Mensagem.objects.filter(session_id=session_id, enviado_por_usuario=True).count()

            # Checa se é a primeira vez (sem mensagens no banco)
            if user_messages == 1: #Mensagem.objects.filter(session_id=session_id).count() == 1:
                Mensagem.objects.create(session_id=session_id, texto="Olá, sou a Vivi da Vila 11. Seja muito bem vindo(a).", enviado_por_usuario=False)
                Mensagem.objects.create(session_id=session_id, texto="🔒 Ao prosseguir, você estará de acordo com os nossos Termos de Uso e nossa Política de Privacidade.", enviado_por_usuario=False)
                Mensagem.objects.create(session_id=session_id, texto="Garantimos que seus dados estão seguros e sendo utilizados apenas para fins relacionados ao atendimento.", enviado_por_usuario=False)
                Mensagem.objects.create(session_id=session_id, texto="Para mais detalhes, acesse: https://vila11.com.br/politica-de-privacidade/", enviado_por_usuario=False)
                Mensagem.objects.create(session_id=session_id, texto="Para seguirmos com seu cadastro em nosso sistema, por favor, poderia me falar seu nome e sobrenome?", enviado_por_usuario=False)
            elif user_messages == 2: #Mensagem.objects.filter(session_id=session_id).count() == 7:
                Mensagem.objects.create(session_id=session_id, texto="E qual é o seu e-mail para que possamos continuar?", enviado_por_usuario=False)
            elif user_messages == 3: #Mensagem.objects.filter(session_id=session_id).count() == 9:
                Mensagem.objects.create(session_id=session_id, texto="Perfeito! Agora, como posso te ajudar hoje?", enviado_por_usuario=False)
            else:
                try:
                    #print("Verificando índice FAISS...")
                    vector_dir = "vector_index"
                    if not os.path.exists(os.path.join(vector_dir, "index.faiss")):
                        resposta_texto = "Erro: índice de conhecimento não encontrado."
                    else:
                        #print("Carregando embeddings e índice FAISS...")
                        openai_key = get_openai_key()
                        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
                        db = FAISS.load_local(
                            vector_dir,
                            embeddings,
                            allow_dangerous_deserialization=True
                        )
                        docs = db.similarity_search(texto_usuario, k=8)
                        contexto = "\n\n".join([doc.page_content for doc in docs])

                        system_prompt = (
                                        f"""Você é um atendente da empresa Vila11 que deve ser humano e responde perguntas sobre contratos, aluguéis e documentos. "
                                        "Responda com base apenas no conteúdo abaixo. Se não houver informação suficiente, diga que não é possível responder com precisão."
                                        "Formate o texto com quebras de linha e parágrafos, se necessário."
                                        "Responda de forma clara e objetiva, evitando jargões técnicos desnecessários.
                                        Se a pergunta for sobre quais unidades estão disponíveis, e você encontrar essa informação no texto, liste os nomes e endereços.
                                        Sempre que o usuário quiser falar com um humano ou falar com um atendente, retorne apenas: "Atendimento Humano".
                                        Sempre que o usuário quiser agendar uma visita, retorne apenas: "Atendimento Humano".
                                        Sempre que o usuário quiser falar com um corretor, retorne apenas: "Atendimento Humano".
                                        Sempre que o usuário quiser encerrar a conversa, sair ou finalizar, retorne apenas: "encerrar conversa".
                                        Quando o cliente quiser mudar de idioma no meio da conversa, seja aderente ao idioma solicitado.
                                        Não ofereça serviços ou comodidades que não estejam na base de conhecimento.
                                        Não fornecer informações de valores e preços, somente quando o cliente perguntar.
                                        Se o cliente falar que o valor esta alto ou muito caro, estimule ele falar qual é o seu orçamento  e ofereça unidades com valor mais aderente ao orçamento do cliente.
                                        Informações sobre pontos de interesse, como terminais de metro, trem, onibus, aeroportos, escolas, hospitais, supermercados, farmácias, padarias, academias e parques, podem ser respondidas com informações fora do contexto.
                                        Não ofereça serviços ou comodidades que não estejam na base de conhecimento.
                                        Sempre que o cliente perguntar o que esta incluso no pacote, ou o que esta incluso no aluguel, responder: Aluguel, Condomínio e IPTU.
                                        Wifi não esta incluso no preço.
                                        Não fornecer informações de valores e preços, somente quando o cliente perguntar.
                                        Conteúdo base:
                                        {contexto}
                                        """
)

                        client = OpenAI(api_key=openai_key)

                        # Histórico da sessão atual
                        mensagens_anteriores = Mensagem.objects.filter(session_id=session_id).order_by('timestamp')
                        historico = [{"role": "system", "content": system_prompt}]

                        # Trunca para as últimas 15 interações (opcional)
                        for msg in list(mensagens_anteriores)[-3:]:
                            historico.append({
                                "role": "user" if msg.enviado_por_usuario else "assistant",
                                "content": msg.texto
                            })

                        # Nova mensagem
                        historico.append({"role": "user", "content": texto_usuario})

                        # Envio para OpenAI
                        response = client.chat.completions.create(
                            model="gpt-4",
                            messages=historico,
                            temperature=0.9,
                            #top_p=0.9,
                            max_tokens=250,
                            #frequency_penalty=0.3,
                            #presence_penalty=0.2
                        )
                        resposta_texto = response.choices[0].message.content

                        #print(f"Resposta gerada com sucesso.: {resposta_texto}")

                except Exception as e:
                    resposta_texto = f"Erro ao gerar resposta: {str(e)}"

                Mensagem.objects.create(session_id=session_id, texto=resposta_texto, enviado_por_usuario=False)


    #mensagens = Mensagem.objects.order_by('timestamp')
    mensagens = Mensagem.objects.filter(session_id=session_id).order_by('timestamp')
    print(f"Número de mensagens na sessão {session_id}: {mensagens.count()}")
    return render(request, 'chat/chatbot.html', {'mensagens': mensagens})


@csrf_exempt
def limpar_historico(request):
    if request.method == 'POST':
        if not request.session.session_key:
            request.session.save()
        session_id = request.session.session_key
        Mensagem.objects.filter(session_id=session_id).delete()
    return redirect('chatbot')

#Parametros CRUD
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

    return JsonResponse({
        'id': parametro.id,
        'chave': parametro.parametroChave,
        'valor': parametro.parametroValor
    })

#Mensagens CRUD
@csrf_exempt
def mensagem_list(request):
    mensagem = Mensagem.objects.all().values('id', 'texto', 'enviado_por_usuario', 'timestamp', 'session_id')  # ou fields conforme seu modelo
    return JsonResponse(list(mensagem), safe=False)


@csrf_exempt
def mensagem_create(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

        form = MensagemForm(data)
        if form.is_valid():
            mensagem = form.save()
            return JsonResponse({
                'id': mensagem.id,
                'texto': mensagem.texto,
                'enviado_por_usuario': mensagem.enviado_por_usuario,
                'session_id': mensagem.session_id,
                'mensagem': 'Mensagem criada com sucesso!'
            }, status=201)
        else:
            return JsonResponse({'errors': form.errors}, status=400)

    return JsonResponse({'error': 'Método não permitido'}, status=405)


@csrf_exempt
def mensagem_update(request, pk):
    parametro = get_object_or_404(Mensagem, pk=pk)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

        form = MensagemForm(data, instance=parametro)
        if form.is_valid():
            mensagem = form.save()
            return JsonResponse({
                'success': True,
                'mensagem': {
                    'id': mensagem.id,
                    'texto': mensagem.texto,
                    'enviado_por_usuario': mensagem.enviado_por_usuario,
                    'session_id': mensagem.session_id
                }
            })
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    else:
        return JsonResponse({
            'id': mensagem.id,
            'texto': mensagem.texto,
            'enviado_por_usuario': mensagem.enviado_por_usuario,
            'session_id': mensagem.session_id
        })


@csrf_exempt
def mensagem_delete(request, pk):
    mensagem = get_object_or_404(Mensagem, pk=pk)

    if request.method == 'POST':
        Mensagem.delete()
        return JsonResponse({
            'success': True,
            'message': f"Mensagem '{mensagem.texto}' excluído com sucesso."
        })

    return JsonResponse({
        'id': mensagem.id,
        'texto': mensagem.texto,
        'enviado_por_usuario': mensagem.enviado_por_usuario,
        'session_id': mensagem.session_id
    })