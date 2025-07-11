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
    print(f"ID da sessão: {session_id}")
    if request.method == 'POST':
        print("Recebendo mensagem do usuário...")
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
                    print("Verificando índice FAISS...")
                    vector_dir = "vector_index"
                    if not os.path.exists(os.path.join(vector_dir, "index.faiss")):
                        resposta_texto = "Erro: índice de conhecimento não encontrado."
                    else:
                        print("Carregando embeddings e índice FAISS...")
                        openai_key = get_openai_key()
                        embeddings = OpenAIEmbeddings(openai_api_key=openai_key)
                        db = FAISS.load_local(
                            vector_dir,
                            embeddings,
                            allow_dangerous_deserialization=True
                        )
                        print("Índice FAISS carregado com sucesso.")

                        print("Buscando contexto relevante...")
                        print(f"Texto do usuário: {texto_usuario}")
                        docs = db.similarity_search(texto_usuario, k=3)
                        print(f"Documentos encontrados: {len(docs)}")
                        contexto = "\n\n".join([doc.page_content for doc in docs])
                        print(f"Contexto encontrado com sucesso.: {contexto}")

                        system_prompt = (
    f"""Você é um assistente virtual da Vila 11, responsável por conversar sobre apartamentos disponíveis para locação.

REGRAS IMPORTANTES (obrigatórias):
1. **NUNCA informe valores** de qualquer tipo **a menos que o usuário pergunte diretamente utilizando as palavras "valor" ou "preço" na pergunta**.
   - Exemplo de pergunta permitida: "Qual é o valor do aluguel?"
   - Exemplo de pergunta NÃO permitida: "Quero saber mais sobre o apartamento" → NÃO RESPONDA COM VALORES.
2. **NUNCA use as palavras "preço", "custo" ou "pacote"**, mesmo se o cliente usar essas palavras. Substitua por:
   - "valor"
   - "o valor total da locação" (quando se referirem a pacote)

3. Se o usuário perguntar **o que está incluído no aluguel** ou no valor, responda sempre:
   - **Aluguel, Condomínio e IPTU estão inclusos. Wifi não está incluso.**

RESPOSTAS AUTOMÁTICAS:
- Se o usuário disser qualquer das seguintes frases, **responda APENAS com o texto indicado**:
  - "Quero falar com um atendente", "falar com um corretor", "agendar uma visita" → **"Atendimento Humano"**
  - "Encerrar", "sair", "finalizar a conversa" → **"encerrar conversa"**
  - "Quero ver fotos", "tem vídeo?", "quero imagens do prédio" → **"Atendimento Humano"**
  - Não sabe responder → **"Desculpe, não consigo falar sobre esses assuntos."**

LIMITAÇÕES:
- Nunca fale sobre **preços ou disponibilidade** com base no site. Essa informação **não está disponível online**.
- Não ofereça serviços ou comodidades além dos confirmados.
- Não ofereça vídeos. Fotos e plantas estão disponíveis no site.

Se o cliente disser que o valor está alto ou caro:
- **NÃO diga valores automaticamente**.
- Responda: "Podemos procurar uma unidade mais alinhada ao seu orçamento. Qual seria o valor ideal para você?"

Se o cliente mudar de idioma no meio da conversa, continue no idioma solicitado.

Você **só pode falar sobre os apartamentos da Vila 11**. Informações sobre pontos de interesse locais (como metrô, mercados, hospitais, parques etc.) podem ser respondidas com base em conhecimento geral.

Sempre finalize suas respostas com uma pergunta para incentivar o usuário a continuar a conversa, em uma nova mensagem.
Exemplos:
- "Você já sabe quantos dormitórios está procurando?"
- "Está planejando a mudança para agora ou para uma data futura?"
- "Prefere qual localização?"
RESPONSABILIDADE DE FORMATO E TOM:
- Mantenha as respostas sempre curtas, diretas e claras (de preferência até 3 parágrafos curtos ou 3 frases).
- Utilize linguagem natural e leve, com um toque simpático e comercial.
- Seja criativo e acolhedor, mas sempre fiel à base de conhecimento.
- Não floreie, nem traga informações genéricas ou vagas.
- Evite repetições e palavras vazias.
"""
)

                        print(system_prompt)

                        print(f"Chave OpenAI usada: {openai_key}")
                        client = OpenAI(api_key=openai_key)

                        print("Gerando resposta com OpenAI...")
                        # Histórico da sessão atual
                        mensagens_anteriores = Mensagem.objects.filter(session_id=session_id).order_by('timestamp')
                        historico = [{"role": "system", "content": system_prompt}]

                        # Trunca para as últimas 15 interações (opcional)
                        for msg in list(mensagens_anteriores)[-15:]:
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
                            temperature=0.5,
                            top_p=0.9,
                            max_tokens=150,
                            frequency_penalty=0.3,
                            presence_penalty=0.2
                        )
                        resposta_texto = response.choices[0].message.content

                        print(f"Resposta gerada com sucesso.: {resposta_texto}")

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