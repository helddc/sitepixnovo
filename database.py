from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    txid = db.Column(db.String(36), unique=True, nullable=False)
    net_amount = db.Column(db.Float, nullable=False)
    charge_amount = db.Column(db.Float, nullable=False)
    payout_pix_key = db.Column(db.String(255), nullable=False)
    payout_pix_key_type = db.Column(db.String(50), nullable=False)  # cpf, email, telefone, aleatoria
