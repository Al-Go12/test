from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/accounts/", include("accounts.urls")),
    path("api/registration/", include("registration.urls")),
    # path("api/payments/", include("payments.urls")),
]
