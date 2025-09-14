from django.db import models
from django.conf import settings 
import uuid

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Personal Details
    full_name = models.CharField(max_length=150)
    aadhaar_number = models.CharField(max_length=12, unique=True) 
    pan_number = models.CharField(max_length=10, unique=True)  

    # Bank Details
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=20)
    ifsc_code = models.CharField(max_length=11) 

    # Address Details
    full_address = models.TextField() 
    contact_number=models.CharField(max_length=10,blank=True,null=True) 
    alternative_contact_number=models.CharField(max_length=10,blank=True,null=True)
    city = models.CharField(max_length=100)
    pin_code = models.CharField(max_length=6) 
    state = models.CharField(max_length=100)   

    loan_type=models.CharField(max_length=100,blank=True,null=True) 
    loan_amount=models.CharField(max_length=7,blank=True,null=True) 

    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)  

    def __str__(self):
        return f"{self.full_name} - {self.pan_number}"

class Registration(models.Model):
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("pending_payment", "Pending Payment"),
        ("paid", "Paid"),
        ("expired", "Expired"),
        ("cancelled", "Cancelled"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile = models.OneToOneField(Profile, on_delete=models.CASCADE)
    application_id = models.CharField(max_length=6, unique=True, default=uuid.uuid4().hex[:6].upper())
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    submitted_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.application_id:
            # Generate a unique 6-digit application ID
            self.application_id = uuid.uuid4().hex[:6].upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Registration: {self.user.phone_number} ({self.status}) - {self.application_id}"



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
