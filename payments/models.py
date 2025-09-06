from django.db import models
from registration.models import Registration
import uuid


class Payment(models.Model):
    STATUS_CHOICES = [
        ("created", "Created"),
        ("authorized", "Authorized"),
        ("captured", "Captured"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name="payments")
    gateway = models.CharField(max_length=20, default="razorpay")
    order_id = models.CharField(max_length=100)
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    amount = models.IntegerField()  # paise for INR
    currency = models.CharField(max_length=10, default="INR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created")
    signature = models.CharField(max_length=256, blank=True, null=True)
    raw_payload = models.JSONField(blank=True, null=True)
    webhook_received_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.gateway} - {self.status} - {self.amount/100:.2f} {self.currency}"
