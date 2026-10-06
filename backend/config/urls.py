from django.contrib import admin
from django.conf import settings
from django.urls import path, re_path
from django.views.static import serve
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
    path('api/clients/<int:client_id>/suspend/', views.suspend_client),
    path('api/clients/<int:client_id>/activate/', views.activate_client),
    path('api/codigos-postales/<str:cp>/', views.postal_code),
    path('api/talleres/', views.workshops),
]
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
