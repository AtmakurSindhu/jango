
# Register your models here.
from django.contrib import admin
from .models import Loan, Transaction

admin.site.register(Loan)
admin.site.register(Transaction)
