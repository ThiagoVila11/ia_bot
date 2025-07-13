from django.db import models

class Mensagem(models.Model):
    texto = models.TextField(verbose_name="Texto da Mensagem")
    enviado_por_usuario = models.BooleanField(verbose_name="Eviado pelo usuário", default=True)
    timestamp = models.DateTimeField(verbose_name="Data/Hora da mensagem", auto_now_add=True)
    session_id = models.CharField(verbose_name="Sessão", max_length=100, default="", blank=None)  # novo campo
    nome = models.CharField(verbose_name="Nome", max_length=100, default="", blank=None)  # novo campo
    email = models.EmailField(verbose_name="Email", default="", blank=None)  # novo campo


class Contexto(models.Model):
    contextoTitulo = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name="Título do Contexto")
    contextoConteudo = models.TextField(verbose_name="Conteúdo do Contexto")
    contextoAtivo = models.DateTimeField(auto_now_add=True, blank=True, null=True, verbose_name="Data/Hora de Ativação")
    contextoAtual = models.BooleanField(default=False, verbose_name="Atual")

    def __str__(self):
        return f"Contexto {self.id} - {self.contextoConteudo[:50]}..."
    
    class Meta:
        verbose_name = "Contexto"
        verbose_name_plural = "Contextos"

class Parametro(models.Model):
    parametroChave = models.CharField(max_length=100, unique=True)
    parametroValor = models.TextField()

    def __str__(self):
        return f"{self.parametroChave}: {self.parametroValor[:50]}..."

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