# database.py
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    txid = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='pending') # pending -> paid -> withdrawn/failed
    net_amount = db.Column(db.Float, nullable=False)
    charge_amount = db.Column(db.Float, nullable=False)
    payout_pix_key = db.Column(db.String(150), nullable=False)
