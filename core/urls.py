from django.urls import path
from .views import responder_pergunta, chatbot, limpar_historico

urlpatterns = [
    path('blip-ia/', responder_pergunta),
    path('', chatbot, name='chatbot'),  # essa linha define a raiz "/"
    path('limpar-historico/', limpar_historico, name='limpar_historico')
]
