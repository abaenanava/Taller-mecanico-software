from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from workshop import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/csrf/', views.csrf),
    path('api/auth/login/', views.login_view),
    path('api/auth/register/', views.register),
    path('api/auth/logout/', views.logout_view),
    path('api/auth/me/', views.me),
    path('api/orders/', views.orders),
    path('api/clients/', views.clients),
    path('api/clients/register/', views.create_client),
    path('api/clients/<int:client_id>/', views.client_detail),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
