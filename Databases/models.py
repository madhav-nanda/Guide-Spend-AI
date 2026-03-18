# models.py
# Flask-SQLAlchemy Models — AI-Powered Financial Management Platform

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ============================================================
# USER MODEL — Week 1 (required for register/login)
# ============================================================
class User(db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50),  nullable=False, unique=True)
    email         = db.Column(db.String(120), nullable=False, unique=True)
    password_hash = db.Column(db.Text,        nullable=False)
    created_at    = db.Column(db.DateTime,    default=datetime.utcnow)

    # Relationships (easy access from a User object)
    transactions         = db.relationship('Transaction',        backref='user', lazy=True, cascade='all, delete')
    budgets              = db.relationship('Budget',             backref='user', lazy=True, cascade='all, delete')
    fraud_logs           = db.relationship('FraudLog',           backref='user', lazy=True, cascade='all, delete')
    savings              = db.relationship('Saving',             backref='user', lazy=True, cascade='all, delete')
    recurring_transactions = db.relationship('RecurringTransaction', backref='user', lazy=True, cascade='all, delete')

    def __repr__(self):
        return f'<User {self.username}>'


# ============================================================
# TRANSACTION MODEL — Week 2
# ============================================================
class Transaction(db.Model):
    __tablename__ = 'transactions'

    id          = db.Column(db.Integer,       primary_key=True)
    user_id     = db.Column(db.Integer,       db.ForeignKey('users.id'), nullable=False)
    amount      = db.Column(db.Numeric(10,2), nullable=False)
    category    = db.Column(db.String(50))
    description = db.Column(db.Text)
    date        = db.Column(db.Date,          nullable=False, default=datetime.utcnow)
    created_at  = db.Column(db.DateTime,      default=datetime.utcnow)

    # Relationships
    fraud_log = db.relationship('FraudLog', backref='transaction', lazy=True)
    saving    = db.relationship('Saving',   backref='source_transaction', lazy=True)

    def __repr__(self):
        return f'<Transaction {self.id} — {self.amount} — {self.category}>'


# ============================================================
# BUDGET MODEL — Week 3
# ============================================================
class Budget(db.Model):
    __tablename__ = 'budgets'

    id           = db.Column(db.Integer,       primary_key=True)
    user_id      = db.Column(db.Integer,       db.ForeignKey('users.id'), nullable=False)
    category     = db.Column(db.String(50),    nullable=False)
    limit_amount = db.Column(db.Numeric(10,2), nullable=False)
    month        = db.Column(db.Integer,       nullable=False)
    year         = db.Column(db.Integer,       nullable=False)
    created_at   = db.Column(db.DateTime,      default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'category', 'month', 'year', name='unique_budget'),
    )

    def __repr__(self):
        return f'<Budget {self.category} — {self.month}/{self.year}>'


# ============================================================
# FRAUD LOG MODEL — Week 4
# ============================================================
class FraudLog(db.Model):
    __tablename__ = 'fraud_logs'

    id               = db.Column(db.Integer,    primary_key=True)
    user_id          = db.Column(db.Integer,    db.ForeignKey('users.id'),        nullable=False)
    transaction_id   = db.Column(db.Integer,    db.ForeignKey('transactions.id'), nullable=False)
    rule_triggered   = db.Column(db.String(100), nullable=False)
    flagged_at       = db.Column(db.DateTime,   default=datetime.utcnow)

    def __repr__(self):
        return f'<FraudLog tx={self.transaction_id} rule={self.rule_triggered}>'


# ============================================================
# SAVING MODEL — Week 4
# ============================================================
class Saving(db.Model):
    __tablename__ = 'savings'

    id                    = db.Column(db.Integer,       primary_key=True)
    user_id               = db.Column(db.Integer,       db.ForeignKey('users.id'),        nullable=False)
    source_transaction_id = db.Column(db.Integer,       db.ForeignKey('transactions.id'), nullable=False)
    rounded_amount        = db.Column(db.Numeric(10,2), nullable=False)
    saved_at              = db.Column(db.DateTime,      default=datetime.utcnow)

    def __repr__(self):
        return f'<Saving {self.rounded_amount} from tx={self.source_transaction_id}>'


# ============================================================
# RECURRING TRANSACTION MODEL — Week 5
# ============================================================
class RecurringTransaction(db.Model):
    __tablename__ = 'recurring_transactions'

    id              = db.Column(db.Integer,       primary_key=True)
    user_id         = db.Column(db.Integer,       db.ForeignKey('users.id'), nullable=False)
    merchant        = db.Column(db.String(100),   nullable=False)
    average_amount  = db.Column(db.Numeric(10,2), nullable=False)
    frequency_days  = db.Column(db.Integer,       nullable=False)
    last_seen       = db.Column(db.Date,          nullable=False)
    annual_estimate = db.Column(db.Numeric(10,2))
    created_at      = db.Column(db.DateTime,      default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'merchant', name='unique_recurring'),
    )

    def __repr__(self):
        return f'<RecurringTransaction {self.merchant} every {self.frequency_days} days>'
