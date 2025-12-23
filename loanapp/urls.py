from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),

    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('give-loan/', views.give_loan, name='give_loan'),

    path('loan/<str:loan_number>/', views.view_loan, name='view_loan'),
    path('loan/<str:loan_number>/pay/', views.pay_loan, name='pay_loan'),
]
