"""
Blueprint registration.
All route modules are registered here and imported by the app factory.
"""
from routes.auth import auth_bp
from routes.transactions import transactions_bp
from routes.plaid import plaid_bp
from routes.insights import insights_bp
from routes.subscriptions import subscriptions_bp
from routes.cashflow import cashflow_bp
from routes.health_score import health_score_bp


def register_blueprints(app):
    """Attach all blueprints to the Flask app."""
    app.register_blueprint(auth_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(plaid_bp, url_prefix="/plaid")
    app.register_blueprint(insights_bp)  # url_prefix defined on blueprint
    app.register_blueprint(subscriptions_bp)  # /v1/subscriptions
    app.register_blueprint(cashflow_bp)  # /v1/cashflow
    app.register_blueprint(health_score_bp)  # /v1/health-score
