from django import forms
from .models import Parametro

class ParametroForm(forms.ModelForm):
    class Meta:
        model = Parametro
        fields = ['parametroChave', 'parametroValor']
        widgets = {
            'parametroValor': forms.Textarea(attrs={'rows': 4}),
        }
