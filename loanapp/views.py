from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from django.utils import timezone
import hashlib

from .models import AppUser, Loan, Transaction, generate_loan_number, generate_transaction_id


# =========================
# PASSWORD HASHING (SIMPLE)
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# =========================
# AUTH HELPERS
# =========================
def get_logged_in_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    return AppUser.objects.filter(user_id=user_id).first()


def login_required_custom(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('user_id'):
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# =========================
# REGISTER
# =========================
def register(request):
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        first = request.POST.get('first_name')
        last = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm = request.POST.get('confirm_password')

        if password != confirm:
            messages.error(request, "Passwords do not match")
            return redirect('register')

        if AppUser.objects.filter(user_id=user_id).exists():
            messages.error(request, "User ID already exists")
            return redirect('register')

        AppUser.objects.create(
            user_id=user_id,
            first_name=first,
            last_name=last,
            email=email,
            phone=phone,
            password=hash_password(password)
        )

        messages.success(request, "Registration successful. Please login.")
        return redirect('login')

    return render(request, 'register.html')


# =========================
# LOGIN
# =========================
def login(request):
    if request.method == "POST":
        user_id = request.POST.get('user_id')
        password = hash_password(request.POST.get('password'))

        user = AppUser.objects.filter(user_id=user_id, password=password).first()
        if not user:
            messages.error(request, "Invalid User ID or Password")
            return redirect('login')

        request.session['user_id'] = user.user_id
        return redirect('dashboard')

    return render(request, 'login.html')


# =========================
# LOGOUT
# =========================
def logout(request):
    request.session.flush()
    return redirect('login')


# =========================
# DASHBOARD
# =========================
@login_required_custom
def dashboard(request):
    user = get_logged_in_user(request)

    loans = Loan.objects.filter(
        Q(lender=user) | Q(borrower=user)
    ).order_by('-loan_created_datetime')

    return render(request, 'dashboard.html', {'loans': loans})


# =========================
# GIVE LOAN (DIRECT PAYMENT)
# =========================
@login_required_custom
def give_loan(request):
    user = get_logged_in_user(request)

    if request.method == "POST":
        to_user_id = request.POST.get('to_user_id')
        principal = float(request.POST.get('principal_amount'))
        interest_rate = float(request.POST.get('monthly_interest_rate'))
        months = int(request.POST.get('loan_months'))

        borrower = AppUser.objects.filter(user_id=to_user_id).first()
        if not borrower:
            messages.error(request, "Borrower User ID not found")
            return redirect('give_loan')

        if borrower == user:
            messages.error(request, "You cannot give loan to yourself")
            return redirect('give_loan')

        total_interest = principal * (interest_rate / 100) * months
        total_amount = principal + total_interest
        monthly_amount = total_amount / months

        loan = Loan.objects.create(
            loan_number=generate_loan_number(),
            lender=user,
            borrower=borrower,
            principal_amount=principal,
            monthly_interest_rate=interest_rate,
            loan_months=months,
            total_interest=total_interest,
            total_amount=total_amount,
            monthly_amount=monthly_amount,
            remaining_amount=total_amount
        )

        messages.success(request, "Loan created successfully")
        return redirect('view_loan', loan_number=loan.loan_number)

    return render(request, 'give_loan.html')


# =========================
# VIEW SINGLE LOAN
# =========================
@login_required_custom
def view_loan(request, loan_number):
    user = get_logged_in_user(request)

    loan = get_object_or_404(
        Loan,
        loan_number=loan_number
    )

    if user not in [loan.lender, loan.borrower]:
        messages.error(request, "Access denied")
        return redirect('dashboard')

    transactions = loan.transactions.all().order_by('-transaction_datetime')

    total_paid = transactions.aggregate(
        total=Sum('paid_amount')
    )['total'] or 0

    return render(request, 'view_loan.html', {
        'loan': loan,
        'transactions': transactions,
        'total_paid': total_paid
    })


# =========================
# PAY LOAN (BORROWER ONLY)
# =========================
@login_required_custom
def pay_loan(request, loan_number):
    user = get_logged_in_user(request)

    loan = get_object_or_404(Loan, loan_number=loan_number)

    if loan.borrower != user:
        messages.error(request, "Only borrower can pay the loan")
        return redirect('dashboard')

    if loan.status == 'COMPLETED':
        messages.error(request, "Loan already completed")
        return redirect('view_loan', loan_number=loan.loan_number)

    if request.method == "POST":
        pay_amount = float(request.POST.get('pay_amount'))

        if pay_amount <= 0:
            messages.error(request, "Invalid payment amount")
            return redirect('pay_loan', loan_number=loan.loan_number)

        if pay_amount > float(loan.remaining_amount):
            messages.error(request, "Payment exceeds remaining balance")
            return redirect('pay_loan', loan_number=loan.loan_number)

        remaining = float(loan.remaining_amount) - pay_amount

        Transaction.objects.create(
            transaction_id=generate_transaction_id(),
            loan=loan,
            paid_amount=pay_amount,
            balance_after=remaining
        )

        loan.remaining_amount = remaining
        if remaining == 0:
            loan.status = 'COMPLETED'
        loan.save()

        messages.success(request, "Payment successful")
        return redirect('view_loan', loan_number=loan.loan_number)

    return render(request, 'pay_loan.html', {'loan': loan})
