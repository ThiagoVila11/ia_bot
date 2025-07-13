from django.contrib import admin
from .models import Parametro, Contexto

@admin.register(Parametro)
class ParametroAdmin(admin.ModelAdmin):
    list_display = ('parametroChave', 'parametroValor')
    search_fields = ('parametroChave',)

@admin.register(Contexto)
class ContextoAdmin(admin.ModelAdmin):
    list_display = ('id', 'contextoTitulo', 'contextoAtual')
    search_fields = ('contextoTitulo', 'contextoConteudo')
