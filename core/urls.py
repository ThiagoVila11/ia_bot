from django.urls import path, include
from .views import responder_pergunta, chatbot, limpar_historico, parametro_list, parametro_create, parametro_update, parametro_delete
from . import views
from django.contrib import admin
from .views import *
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'unidades', UnidadeViewSet)
router.register(r'leads', leadViewSet)
router.register(r'consultores', ConsultorViewSet)
router.register(r'parametros', ParametroViewSet)
router.register(r'contextos', ContextoViewSet)
router.register(r'mensagens', MensagemViewSet)

urlpatterns = [
    path('blip-ia/', responder_pergunta),
    path('', chatbot, name='chatbot'),  # essa linha define a raiz "/"
    path('limpar-historico/', limpar_historico, name='limpar_historico'),
    path('', include(router.urls)),  # isso expande as rotas do ViewSet
    # Parâmetro URLs
    path('parametros/', views.parametro_list, name='parametro_list'),
    path('parametros/novo/', views.parametro_create, name='parametro_create'),
    path('parametros/<int:pk>/editar/', views.parametro_update, name='parametro_update'),
    path('parametros/<int:pk>/excluir/', views.parametro_delete, name='parametro_delete'),
    #mensagem URLs
    path('mensagens/', views.mensagem_list, name='mensagens_list'),
    path('mensagens/novo/', views.mensagem_create, name='mensagens_create'),
    path('mensagens/<int:pk>/editar/', views.mensagem_update, name='mensagens_update'),
    path('mensagens/<int:pk>/excluir/', views.mensagem_delete, name='mensagens_delete'),
    path('sessoes/<str:session_id>/excluir/', views.excluir_conversa, name='excluir_conversa'),
    # parametros urls
    path('parametros/', views.parametro_list, name='parametro_list'),
    #path('parametros/', views.listar_parametros, name='listar_parametros'),
    path('parametros/adicionar/', views.adicionar_parametro, name='adicionar_parametro'),
    path('parametros/<int:pk>/editar/', views.alterar_parametro, name='alterar_parametro'),
    path('parametros/<int:pk>/excluir/', views.parametro_delete, name='excluir_parametro'),
    # paginas html
    path('sessoes/', views.lista_sessoes, name='lista_sessoes'),
    path('ver_conversa/<str:session_id>/', views.ver_conversa, name='ver_conversa'),
    path('enviar_conversa/<str:session_id>/', views.enviar_conversa, name='enviar_conversa'),
    #contextos urls
    path('contextos/', views.listar_contextos, name='listar_contextos'),
    path('contextos/adicionar/', views.contexto_adicionar, name='contexto_adicionar'),
    path('contextos/<int:id>/', views.contexto_consultar, name='contexto_consultar'),
    path('contextos/<int:id>/alterar/', views.contexto_alterar, name='contexto_alterar'),
    path('contextos/<int:id>/excluir/', views.contexto_excluir, name='contexto_excluir'),
    # Consultor URLs
    path('consultores/', views.listar_consultor, name='listar_consultor'),
    path('consultores/adicionar/', views.adicionar_consultor, name='adicionar_consultor'),
    path('consultores/<int:pk>/alterar/', views.alterar_consultor, name='alterar_consultor'),
    path('consultores/<int:pk>/excluir/', views.excluir_consultor, name='excluir_consultor'),
    #funções do chatbot
    path('inatividade/', views.mensagem_inatividade, name='mensagem_inatividade'),
    #twilio urls
    path('whatsapp/', views.webhook_twilio, name='webhook_twilio'),
    path('enviar-mensagem/', views.enviar_mensagem, name='enviar-mensagem'),
    #leads urls
    path('leads/', views.listar_leads, name='listar_leads'),
    path('leads/adicionar/', views.adicionar_lead, name='adicionar_lead'),
] 
