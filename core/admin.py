from django.contrib import admin
from .models import Parametro, Contexto, Mensagem, Consultor, lead

@admin.register(Parametro)
class ParametroAdmin(admin.ModelAdmin):
    list_display = ('parametroChave', 'parametroValor')
    search_fields = ('parametroChave',)

@admin.register(Contexto)
class ContextoAdmin(admin.ModelAdmin):
    list_display = ('id', 'contextoTitulo', 'contextoAtual')
    search_fields = ('contextoTitulo', 'contextoConteudo')

@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ('texto', 'enviado_por_usuario', 'timestamp', 'session_id',
                    'nome', 'email', 'prompt_tokens', 'completion_tokens',
                    'total_tokens', 'custo_estimado')
    search_fields = ('texto', 'nome', 'email', 'session_id')

@admin.register(Consultor)
class ConsultorAdmin(admin.ModelAdmin):
    list_display = ('consultorNome', 'consultorEmail', 'consultorTelefone', 'consultorAtivo')
    search_fields = ('consultorNome', 'consultorEmail', 'consultorTelefone', 'consultorAtivo')

@admin.register(lead)
class leadAdmin(admin.ModelAdmin):
    list_display = ('leadNome', 'leadEmail', 'leadTelefone', 'leadDataHoraCriacao', 'leadAtivo', 'leadConsultor', 'leadIntegrado')
    search_fields = ('leadNome', 'leadEmail', 'leadTelefone')