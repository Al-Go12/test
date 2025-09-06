from django.urls import path
from .views import (ProfileAPIView,AdminProfileListView,DashboardAPIView,                    
AdminProfileExportExcelView,CashfreeCreateOrderView,
CashfreePaymentWebhookView,RegistrationStatusAPIView, 
UserApplicationAPIView,CashfreePaymentStatusView
) 



urlpatterns = [
    path("profile/", ProfileAPIView.as_view(), name="user-profile"),  
    path('registration/status/', RegistrationStatusAPIView.as_view(), name='registration-status'),
    path("application/", UserApplicationAPIView.as_view(), name="user-application"),










    path("admin/profiles/", AdminProfileListView.as_view(), name="admin-profiles"), 
    path("admin/dashboard/", DashboardAPIView.as_view(), name="dashboard-api"), 
    path("admin/profiles/export/", AdminProfileExportExcelView.as_view(), name="admin-profile-export"), 
    path('cashfree/create-order/', CashfreeCreateOrderView.as_view(), name='cashfree-create-order'),  
    path("cashfree-status/<str:order_id>/", CashfreePaymentStatusView.as_view(), name="cashfree-payment-status"),
    path('cashfree/webhook/', CashfreePaymentWebhookView.as_view(), name='cashfree-webhook'),
]
