from django.db import models

class Mensagem(models.Model):
    texto = models.TextField(verbose_name="Texto da Mensagem")
    enviado_por_usuario = models.BooleanField(verbose_name="Eviado pelo usuário", default=True)
    timestamp = models.DateTimeField(verbose_name="Data/Hora da mensagem", auto_now_add=True)
    session_id = models.CharField(verbose_name="Sessão", max_length=100, default="", blank=None)  # novo campo
    nome = models.CharField(verbose_name="Nome", max_length=100, default="", blank=None)  # novo campo
    email = models.EmailField(verbose_name="Email", default="", blank=None)  # novo campo
    prompt_tokens = models.IntegerField(verbose_name="Tokens de Prompt", default=0, blank=True, null=True)
    completion_tokens = models.IntegerField(verbose_name="Tokens de Conclusão", default=0, blank=True, null=True)
    total_tokens = models.IntegerField(verbose_name="Tokens Totais", default=0, blank=True, null=True)
    custo_estimado = models.DecimalField(verbose_name="Custo Estimado", max_digits=10, decimal_places=6, default=0.0, blank=True, null=True)


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
    consultorNome = models.CharField(verbose_name='Nome', max_length=100)
    consultorEmail = models.EmailField(verbose_name='Email', unique=True)
    consultorTelefone = models.CharField(verbose_name='Telefone', max_length=15, blank=True, null=True)
    consultorAtivo = models.BooleanField(verbose_name='Ativo', default=True)

    def __str__(self):
        return self.consultorNome

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

class lead(models.Model):
    leadNome = models.CharField(verbose_name='Nome', max_length=100)
    leadEmail = models.EmailField(verbose_name='Email', unique=True)
    leadTelefone = models.CharField(verbose_name='Telefone', max_length=15, blank=True, null=True)
    leadDataHoraCriacao = models.DateTimeField('Data/Hora criação do lead', auto_now_add=True)
    leadAtivo = models.BooleanField(verbose_name='Ativo', default=True)
    leadConsultor = models.ForeignKey(Consultor, verbose_name='Consultor', on_delete=models.CASCADE, related_name='leads', blank=True, null=True)
    leadIntegrado = models.BooleanField(default=False, verbose_name="Integrado com CRM")

    def __str__(self):
        return self.leadNome

    class Meta:
        verbose_name = "Lead"
        verbose_name_plural = "Leads"