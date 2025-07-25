from rest_framework import serializers
from .models import *

class UnidadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unidade
        fields = '__all__'

class leadSerializer(serializers.ModelSerializer):
    class Meta:
        model = lead
        fields = '__all__'

class ConsultorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultor
        fields = '__all__'

class ParametroSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parametro
        fields = '__all__'

class ContextoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contexto
        fields = '__all__'

class MensagemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mensagem
        fields = '__all__'