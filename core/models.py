from django.db import models

class Mensagem(models.Model):
    texto = models.TextField()
    enviado_por_usuario = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
