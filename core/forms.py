from django import forms
from .models import Parametro, Mensagem, Contexto, lead, Consultor

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

class leadForm(forms.ModelForm):
    class Meta:
        model = lead
        fields = ['leadNome', 'leadEmail', 'leadTelefone', 'leadAtivo',  
                  'leadConsultor', 'leadIntegrado']
        widgets = {
            'leadAtivo': forms.CheckboxInput(),
            'leadIntegrado': forms.CheckboxInput(),
        }

class ConsultorForm(forms.ModelForm):
    class Meta:
        model = Consultor
        fields = ['consultorNome', 'consultorEmail', 'consultorTelefone', 'consultorAtivo']
        widgets = {
            'consultorAtivo': forms.CheckboxInput(),
        }