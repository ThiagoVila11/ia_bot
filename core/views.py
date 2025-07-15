import json
import os
import xml.etree.ElementTree as ET
import requests
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
from .models import Parametro, Contexto
from .forms import ParametroForm, MensagemForm, ContextoForm
from django.db.models import Max, Sum
from django.contrib import messages
from django.utils import timezone
from twilio.rest import Client
from django.http import HttpResponse
from rest_framework.decorators import api_view



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

    if request.session.get('session_id') is None:
        request.session.save()
        request.session['session_id'] = request.session.session_key
        print("Sessão criada e ID salvo na sessão.")

    #if not request.session.session_key:
    #    request.session.save()  # garante que a sessão seja criada
    #    request.session['session_id'] = request.session.session_key
        
    session_id = request.session.get('session_id')  #request.session.session_key
    print(f"ID da sessão atual: {session_id}")


    if request.session.get('email_usuario') is None:
        request.session['email_usuario'] = "nao@informado.com.br"

    if request.session.get('nome_usuario') is None:
        request.session['nome_usuario'] = "Usuário Anônimo"

    if request.method == 'POST':
        #print("Recebendo mensagem do usuário...")
        texto_usuario = request.POST.get('mensagem')
        if texto_usuario:
            Mensagem.objects.create(session_id=session_id, texto=texto_usuario, enviado_por_usuario=True, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
            idmensagem = Mensagem.objects.filter(session_id=session_id, enviado_por_usuario=True).last().id
            print(f"Mensagem do usuário recebida: {texto_usuario} (ID: {idmensagem})")
            cliente_messages = Mensagem.objects.filter(session_id=session_id, enviado_por_usuario=True).count()
            nrmsg = Mensagem.objects.filter(session_id=session_id).count()
            #print(f"Número de mensagens totais: {nrmsg} + {texto_usuario}")
            
            if cliente_messages == 2:
                #mensagem = Mensagem.objects.get(id=idmensagem)
                #mensagem.nome = texto_usuario
                #mensagem.save()
                Mensagem.objects.filter(session_id=session_id).update(nome=texto_usuario)
                request.session['nome_usuario'] = texto_usuario  # 🔹 salva na sessão
            elif cliente_messages == 3:
                #mensagem = Mensagem.objects.get(id=idmensagem)
                #mensagem.email = texto_usuario
                #mensagem.save()
                Mensagem.objects.filter(session_id=session_id).update(email=texto_usuario)
                request.session['email_usuario'] = texto_usuario  # 🔹 salva na sessão


            print(f"Número de mensagens cliente: {cliente_messages} + {texto_usuario}")
                
            if Mensagem.objects.filter(session_id=session_id).count() == 1:
                Mensagem.objects.create(session_id=session_id, texto="Olá, sou a Vivi da Vila 11. Seja muito bem vindo(a).", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                Mensagem.objects.create(session_id=session_id, texto="🔒 Ao prosseguir, você estará de acordo com os nossos Termos de Uso e nossa Política de Privacidade.", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                Mensagem.objects.create(session_id=session_id, texto="Garantimos que seus dados estão seguros e sendo utilizados apenas para fins relacionados ao atendimento.", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                Mensagem.objects.create(session_id=session_id, texto="Para mais detalhes, acesse: https://vila11.com.br/politica-de-privacidade/", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                Mensagem.objects.create(session_id=session_id, texto="Para seguirmos com seu cadastro em nosso sistema, por favor, poderia me falar seu nome e sobrenome?", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
            elif Mensagem.objects.filter(session_id=session_id).count() == 7:
                Mensagem.objects.create(session_id=session_id, texto="E qual é o seu e-mail para que possamos continuar?", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
            elif Mensagem.objects.filter(session_id=session_id).count() == 9:
                Mensagem.objects.create(session_id=session_id, texto="Perfeito! Agora, como posso te ajudar hoje?", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
            else:
                try:
                    vector_dir = "vector_index"
                    if not os.path.exists(os.path.join(vector_dir, "index.faiss")):
                        resposta_texto = "Erro: índice de conhecimento não encontrado."
                    else:
                        #busca contexto no banco de dados
                        contexto_escrito = Contexto.objects.filter(contextoAtual=True).first()

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
                                        f"""{contexto_escrito}
                                        Conteúdo base:
                                        {contexto}
                                        """)
                        print(f"Contexto usado: {contexto_escrito}")
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
                        # Recupera uso de tokens
                        prompt_tokens = response.usage.prompt_tokens
                        completion_tokens = response.usage.completion_tokens
                        total_tokens = response.usage.total_tokens

                        # Calcula custo estimado (valores em dólar para gpt-4 em julho/2025)
                        # Para gpt-4-turbo use $0.01 e $0.03
                        prompt_cost = prompt_tokens * 0.001 / 1000
                        completion_cost = completion_tokens * 0.015 / 1000
                        total_cost = prompt_cost + completion_cost

                except Exception as e:
                    resposta_texto = f"Erro ao gerar resposta: {str(e)}"

                Mensagem.objects.create(session_id=session_id, texto=resposta_texto, 
                                        enviado_por_usuario=False, nome=request.session.get('nome_usuario'),
                                         email=request.session.get('email_usuario'),
                                         prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                                         total_tokens=total_tokens, custo_estimado=total_cost)
                
                if resposta_texto.lower() in ["encerrar conversa", "sair", "finalizar"]:
                    Mensagem.objects.create(session_id=session_id, texto="Conversa encerrada. Até logo!", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                    return redirect('chatbot')
                
                if resposta_texto.lower() == "atendimento humano":
                    Mensagem.objects.create(session_id=session_id, texto="Encaminhando para atendimento humano...", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                    return redirect('chatbot')
                
    mensagens = Mensagem.objects.filter(session_id=session_id).order_by('timestamp')
    print(f"Número de mensagens na sessão {session_id}: {mensagens.count()}")
    return render(request, 'chat/chatbot.html', {'mensagens': mensagens})


@csrf_exempt
def limpar_historico(request):
    session_id = request.session.get('session_id')
    if request.method == 'POST':
        #session_id = request.session.session_key
        Mensagem.objects.filter(session_id=session_id).delete()
    return redirect('chatbot')

#Parametros CRUD
@csrf_exempt
def parametro_list(request):
    parametros = Parametro.objects.all()
    return render(request, 'chat/parametro_list.html', {'parametros': parametros})


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

#paginas da web

def lista_sessoes(request):
    sessoes = (
        Mensagem.objects
        .values('session_id')
        .annotate(
            nome=Max('nome'),
            email=Max('email'),
            prompt_tokens=Sum('prompt_tokens'),
            completion_tokens=Sum('completion_tokens'),
            total_tokens=Sum('total_tokens'),
            custo_estimado=Sum('custo_estimado')
        )
        .order_by('-session_id')
    )
    return render(request, 'chat/sessoes.html', {'sessoes': sessoes})

def ver_conversa(request, session_id):
    mensagens = Mensagem.objects.filter(session_id=session_id).order_by('timestamp')
    return render(request, 'chat/ver_conversa.html', {'mensagens': mensagens, 'session_id': session_id})

def enviar_conversa(request, session_id):
    if request.method == "POST":
        # Aqui você pode processar a conversa, enviar por email, salvar PDF, etc.
        #messages.success(request, f"Conversa da sessão {session_id} enviada com sucesso!")
        print(f"Conversa da sessão {session_id} enviada com sucesso!")
    return redirect('lista_sessoes')

def excluir_conversa(request, session_id):
    if request.method == "POST":
        Mensagem.objects.filter(session_id=session_id).delete()
        messages.success(request, "Conversa excluída com sucesso.")
    return redirect('lista_sessoes')

def listar_contextos(request):
    contextos = Contexto.objects.all().order_by('-contextoAtivo')
    return render(request, 'chat/lista_contextos.html', {'contextos': contextos})

def contexto_adicionar(request):
    if request.method == 'POST':
        form = ContextoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_contextos')  # ajuste para sua URL de lista
    else:
        form = ContextoForm()
    return render(request, 'chat/contexto_adicionar.html', {'form': form})

def contexto_consultar(request, id):
    contexto = get_object_or_404(Contexto, id=id)
    return render(request, 'chat/contexto_detalhe.html', {'contexto': contexto})

def contexto_alterar(request, id):
    contexto = get_object_or_404(Contexto, id=id)
    if request.method == 'POST':
        form = ContextoForm(request.POST, instance=contexto)
        if form.is_valid():
            form.save()
            return redirect('listar_contextos')
    else:
        form = ContextoForm(instance=contexto)
    return render(request, 'chat/contexto_form.html', {'form': form, 'contexto': contexto})

def contexto_excluir(request, id):
    contexto = get_object_or_404(Contexto, id=id)
    if request.method == 'POST':
        contexto.delete()
        return redirect('listar_contextos')
    return render(request, 'chat/contexto_confirmar_exclusao.html', {'contexto': contexto})

# Parametros CRUD
def listar_parametros(request):
    parametros = Parametro.objects.all()
    return render(request, 'parametros/listar.html', {'parametros': parametros})

def adicionar_parametro(request):
    if request.method == 'POST':
        form = ParametroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_parametros')
    else:
        form = ParametroForm()
    return render(request, 'parametros/form.html', {'form': form, 'titulo': 'Adicionar Parâmetro'})

def alterar_parametro(request, pk):
    parametro = get_object_or_404(Parametro, pk=pk)
    if request.method == 'POST':
        form = ParametroForm(request.POST, instance=parametro)
        if form.is_valid():
            form.save()
            return redirect('listar_parametros')
    else:
        form = ParametroForm(instance=parametro)
    return render(request, 'parametros/form.html', {'form': form, 'titulo': 'Alterar Parâmetro'})

def excluir_parametro(request, pk):
    parametro = get_object_or_404(Parametro, pk=pk)
    if request.method == 'POST':
        parametro.delete()
        return redirect('listar_parametros')
    return render(request, 'parametros/confirmar_exclusao.html', {'parametro': parametro})

def mensagem_inatividade(request):
    if request.method == 'POST':
        session_id = request.session.get('session_id') #request.session.session_key or request.session.save()
        texto = "Percebi que tem um tempinho que paramos de conversar. Precisa de mais alguma ajuda em nossa conversa?"

        # Salva no histórico (opcional)
        Mensagem.objects.create(
            session_id=session_id,
            enviado_por_usuario=False,
            texto=texto,
            email=request.session.get('email_usuario'),
            nome=request.session.get('nome_usuario')
        )   

        return JsonResponse({'texto': texto})
    
    
def enviar_mensagem(numero_destino, mensagem_texto):
    account_sid = 'SACa7493a9fd84fe39c5abc3f17a2ee6a7e'
    auth_token = '2d83bf9cf9a7ee4709af8d88bf9301fe'
    from_whatsapp_number = 'whatsapp:+14155238886'
    to_whatsapp_number = f'whatsapp:{numero_destino}'

    client = Client(account_sid, auth_token)

    message = client.messages.create(
        body=mensagem_texto,
        from_=from_whatsapp_number,
        to=to_whatsapp_number
    )

    return message.sid

ACCOUNT_SID = Parametro.objects.get(parametroChave='ACCOUNT_SID').parametroValor
AUTH_TOKEN = Parametro.objects.get(parametroChave='AUTH_TOKEN').parametroValor
FROM_WHATSAPP_NUMBER = Parametro.objects.get(parametroChave='FROM_WHATSAPP_NUMBER').parametroValor

@csrf_exempt
@api_view(['POST'])
def enviar_mensagem(request):
    numero_destino = request.data.get('numero')
    mensagem_texto = request.data.get('mensagem')

    if not numero_destino or not mensagem_texto:
        return Response({'erro': 'Campos "numero" e "mensagem" são obrigatórios.'}, status=400)

    try:
        client = Client(ACCOUNT_SID, AUTH_TOKEN)
        message = client.messages.create(
            body=mensagem_texto,
            from_=FROM_WHATSAPP_NUMBER,
            to=f'whatsapp:{numero_destino}'
        )
        return Response({'status': 'Mensagem enviada', 'sid': message.sid})
    except Exception as e:
        return Response({'erro': str(e)}, status=500)

def gerar_resposta(request, mensagem, remetente):
    print("Gerando resposta para a mensagem...")
    # Aqui você pode colocar chamada à OpenAI, regras ou qualquer lógica
    if request.session.get('session_id') is None:
            request.session.save()
            request.session['session_id'] = request.session.session_key
            print("Sessão criada e ID salvo na sessão.")
            
            session_id = request.session.get('session_id')  #request.session.session_key
            print(f"ID da sessão atual: {session_id}")


    if request.session.get('email_usuario') is None:
        request.session['email_usuario'] = "nao@informado.com.br"

    if request.session.get('nome_usuario') is None:
        request.session['nome_usuario'] = "Usuário Anônimo"

    if request.method == 'POST':
        print("Recebendo mensagem do usuário...")
        texto_usuario = request.POST.get('mensagem')
        if texto_usuario:
            Mensagem.objects.create(session_id=session_id, texto=texto_usuario, enviado_por_usuario=True, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
            idmensagem = Mensagem.objects.filter(session_id=session_id, enviado_por_usuario=True).last().id
            print(f"Mensagem do usuário recebida: {texto_usuario} (ID: {idmensagem})")
            cliente_messages = Mensagem.objects.filter(session_id=session_id, enviado_por_usuario=True).count()
            nrmsg = Mensagem.objects.filter(session_id=session_id).count()
            
            if cliente_messages == 2:
                Mensagem.objects.filter(session_id=session_id).update(nome=texto_usuario)
                request.session['nome_usuario'] = texto_usuario  # 🔹 salva na sessão
            elif cliente_messages == 3:
                Mensagem.objects.filter(session_id=session_id).update(email=texto_usuario)
                request.session['email_usuario'] = texto_usuario  # 🔹 salva na sessão


            print(f"Número de mensagens cliente: {cliente_messages} + {texto_usuario}")
                
            if Mensagem.objects.filter(session_id=session_id).count() == 1:
                Mensagem.objects.create(session_id=session_id, texto="Olá, sou a Vivi da Vila 11. Seja muito bem vindo(a).", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                Mensagem.objects.create(session_id=session_id, texto="🔒 Ao prosseguir, você estará de acordo com os nossos Termos de Uso e nossa Política de Privacidade.", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                Mensagem.objects.create(session_id=session_id, texto="Garantimos que seus dados estão seguros e sendo utilizados apenas para fins relacionados ao atendimento.", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                Mensagem.objects.create(session_id=session_id, texto="Para mais detalhes, acesse: https://vila11.com.br/politica-de-privacidade/", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                Mensagem.objects.create(session_id=session_id, texto="Para seguirmos com seu cadastro em nosso sistema, por favor, poderia me falar seu nome e sobrenome?", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                url = "http://10.1.10.86:8003/enviar-mensagem/"  # Troque pelo seu endereço
                payload = {
                    "numero": "+5511986266981",  # Número de destino (formato internacional)
                    "mensagem": f"""🔒 Ao prosseguir, você estará de acordo com os nossos Termos de Uso e nossa Política de Privacidade.
                                Garantimos que seus dados estão seguros e sendo utilizados apenas para fins relacionados ao atendimento.
                                Para mais detalhes, acesse: https://vila11.com.br/politica-de-privacidade/
                                Para seguirmos com seu cadastro em nosso sistema, por favor, poderia me falar seu nome e sobrenome?"""
                }
                response = requests.post(url, json=payload)
                print("Status:", response.status_code)
                print("Resposta:", response.json())
            
            
            elif Mensagem.objects.filter(session_id=session_id).count() == 7:
                Mensagem.objects.create(session_id=session_id, texto="E qual é o seu e-mail para que possamos continuar?", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
            elif Mensagem.objects.filter(session_id=session_id).count() == 9:
                Mensagem.objects.create(session_id=session_id, texto="Perfeito! Agora, como posso te ajudar hoje?", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
            else:
                try:
                    vector_dir = "vector_index"
                    if not os.path.exists(os.path.join(vector_dir, "index.faiss")):
                        resposta_texto = "Erro: índice de conhecimento não encontrado."
                    else:
                        #busca contexto no banco de dados
                        contexto_escrito = Contexto.objects.filter(contextoAtual=True).first()

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
                                        f"""{contexto_escrito}
                                        Conteúdo base:
                                        {contexto}
                                        """)
                        print(f"Contexto usado: {contexto_escrito}")
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
                        # Recupera uso de tokens
                        prompt_tokens = response.usage.prompt_tokens
                        completion_tokens = response.usage.completion_tokens
                        total_tokens = response.usage.total_tokens

                        # Calcula custo estimado (valores em dólar para gpt-4 em julho/2025)
                        # Para gpt-4-turbo use $0.01 e $0.03
                        prompt_cost = prompt_tokens * 0.001 / 1000
                        completion_cost = completion_tokens * 0.015 / 1000
                        total_cost = prompt_cost + completion_cost

                except Exception as e:
                    resposta_texto = f"Erro ao gerar resposta: {str(e)}"

                Mensagem.objects.create(session_id=session_id, texto=resposta_texto, 
                                        enviado_por_usuario=False, nome=request.session.get('nome_usuario'),
                                        email=request.session.get('email_usuario'),
                                        prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
                                        total_tokens=total_tokens, custo_estimado=total_cost)
                
                if resposta_texto.lower() in ["encerrar conversa", "sair", "finalizar"]:
                    Mensagem.objects.create(session_id=session_id, texto="Conversa encerrada. Até logo!", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                    return redirect('chatbot')
                
                if resposta_texto.lower() == "atendimento humano":
                    Mensagem.objects.create(session_id=session_id, texto="Encaminhando para atendimento humano...", enviado_por_usuario=False, nome=request.session.get('nome_usuario'), email=request.session.get('email_usuario'))
                    return redirect('chatbot')
                
        mensagens = Mensagem.objects.filter(session_id=session_id).order_by('timestamp')
        print(f"Número de mensagens na sessão {session_id}: {mensagens.count()}")
        #return render(request, 'chat/chatbot.html', {'mensagens': mensagens})
        resposta = f"Olá {remetente}, recebi sua mensagem: {resposta_texto}"

    resposta = f"Olá {remetente}, recebi sua mensagem: {mensagem}"
    return resposta


@csrf_exempt
def webhook_twilio(request):
    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido"}, status=405)

    try:
        # Verifica se o corpo é JSON
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body.decode('utf-8'))
            except json.JSONDecodeError:
                return JsonResponse({"erro": "JSON inválido"}, status=400)
            mensagem = data.get("Body")
            remetente = data.get("From")
        else:
            # Trata como x-www-form-urlencoded (como o Twilio envia)
            mensagem = request.POST.get("Body")
            remetente = request.POST.get("From")

        if not mensagem or not remetente:
            return JsonResponse({"erro": "Dados incompletos"}, status=400)

        print(f"Mensagem recebida de {remetente}: {mensagem}")

        # Sua lógica de resposta aqui (função que gera a resposta)
        resposta = gerar_resposta(request, mensagem, remetente)
        print(f"Resposta gerada: {resposta}")

        return JsonResponse({"resposta": resposta}, status=200)

    except Exception as e:
        return JsonResponse({"erro": str(e)}, status=500)