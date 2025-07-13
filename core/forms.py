from django import forms
from .models import Parametro, Mensagem, Contexto

class ParametroForm(forms.ModelForm):
    class Meta:
        model = Parametro
        fields = ['parametroChave', 'parametroValor']
        widgets = {
            'parametroValor': forms.Textarea(attrs={'rows': 4}),
        }

class MensagemForm(forms.ModelForm):
    class Meta:
        model = Mensagem
        fields = ['texto', 'enviado_por_usuario', 'session_id']
        widgets = {
            'texto': forms.Textarea(attrs={'rows': 4}),
        }

class ContextoForm(forms.ModelForm):
    class Meta:
        model = Contexto
        fields = ['contextoTitulo', 'contextoConteudo', 'contextoAtual']
        widgets = {
            'contextoConteudo': forms.Textarea(attrs={'rows': 15}),
            'contextoAtual': forms.CheckboxInput(),
        }