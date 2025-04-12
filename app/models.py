from django.db import models

class UserRegistration(models.Model):
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=15)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    def approve(self):
        self.status = 'approved'
        self.save()
        
    def reject(self):
        self.status = 'rejected'
        self.save()

class Batch(models.Model):
    date = models.DateField()
    time = models.TimeField()
    max_participants = models.IntegerField()
    message_template = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class BatchAssignment(models.Model):
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE)
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(auto_now_add=True)

class WhatsAppMessage(models.Model):
    recipient = models.CharField(max_length=20)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pendente'), ('sent', 'Enviado'), ('delivered', 'Entregue'), 
                 ('read', 'Lido'), ('failed', 'Falhou'), ('received', 'Recebida')],
        default='pending'
    )
    user = models.ForeignKey(UserRegistration, on_delete=models.CASCADE, null=True, blank=True)
    wamid = models.CharField(max_length=255, blank=True, null=True, help_text="ID da mensagem WhatsApp para rastreamento de status")
    
    def __str__(self):
        return f"Mensagem para {self.recipient} em {self.timestamp}"
