from django.urls import path
from .views import responder_pergunta, chatbot, limpar_historico, parametro_list, parametro_create, parametro_update, parametro_delete
from . import views

urlpatterns = [
    path('blip-ia/', responder_pergunta),
    path('', chatbot, name='chatbot'),  # essa linha define a raiz "/"
    path('limpar-historico/', limpar_historico, name='limpar_historico'),
    path('parametros/', views.parametro_list, name='parametro_list'),
    path('parametros/novo/', views.parametro_create, name='parametro_create'),
    path('parametros/<int:pk>/editar/', views.parametro_update, name='parametro_update'),
    path('parametros/<int:pk>/excluir/', views.parametro_delete, name='parametro_delete'),
]
