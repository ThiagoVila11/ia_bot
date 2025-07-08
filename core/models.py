from django.db import models

class Mensagem(models.Model):
    texto = models.TextField()
    enviado_por_usuario = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

class Contexto(models.Model):
    contextoConteudo = models.TextField()
    contextoAtivo = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Contexto {self.id} - {self.contextoConteudo[:50]}..."
    
    class Meta:
        verbose_name = "Contexto"
        verbose_name_plural = "Contextos"

class Parametro(models.Model):
    parametroChave = models.CharField(max_length=100, unique=True)
    parametroValor = models.TextField()

    def __str__(self):
        return f"{self.chave}: {self.valor[:50]}..."

    class Meta:
        verbose_name = "Parâmetro"
        verbose_name_plural = "Parâmetros"

class Consultor(models.Model):
    consultorNome = models.CharField(max_length=100)
    consultorEmail = models.EmailField(unique=True)
    consultorTelefone = models.CharField(max_length=15, blank=True, null=True)
    consultorAtivo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

    class Meta:
        verbose_name = "Consultor"
        verbose_name_plural = "Consultores"

class Conversa(models.Model):
    conversaEmailCliente = models.EmailField()
    conversaTextoCliente = models.TextField()
    conversaTextoResposta = models.TextField(blank=True, null=True)
    conversaDataHora = models.DateTimeField(auto_now_add=True)
    conversaAtiva = models.BooleanField(default=True)

    def __str__(self):
        return f"Conversa {self.id} - Consultor: {self.conversaConsultor.nome}"

    class Meta:
        verbose_name = "Conversa"
        verbose_name_plural = "Conversas"