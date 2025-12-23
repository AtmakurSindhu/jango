from django.db import models
from django.utils import timezone
import uuid


# =========================
# USER TABLE (MANUAL USER ID)
# =========================
class AppUser(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    password = models.CharField(max_length=255)  # store hashed password
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user_id


# =========================
# LOAN TABLE (GIVE LOAN)
# =========================
class Loan(models.Model):
    loan_number = models.CharField(max_length=50, unique=True)

    lender = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='loans_given'
    )

    borrower = models.ForeignKey(
        AppUser,
        on_delete=models.CASCADE,
        related_name='loans_taken'
    )

    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    loan_months = models.PositiveIntegerField()

    total_interest = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    monthly_amount = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=[('ACTIVE', 'ACTIVE'), ('COMPLETED', 'COMPLETED')],
        default='ACTIVE'
    )

    loan_created_datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.loan_number


# =========================
# TRANSACTION TABLE (PAY LOAN)
# =========================
class Transaction(models.Model):
    transaction_id = models.CharField(max_length=60, unique=True)

    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    paid_amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_after = models.DecimalField(max_digits=12, decimal_places=2)

    transaction_datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.transaction_id


# =========================
# HELPER FUNCTIONS
# =========================
def generate_loan_number():
    return f"LN-{timezone.now().strftime('%Y%m%d%H%M%S')}"


def generate_transaction_id():
    return f"TXN-{timezone.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:5]}"
