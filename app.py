# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import uuid
import os

from config import FIXED_FEE, PERCENTAGE_COMMISSION, MINIMUM_VALUE
from database import db, Transaction
from anubis import create_pix_charge, send_pix_payout

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///transactions.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.urandom(24)
db.init_app(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            payout_pix_key = request.form['payout_pix_key']
            payout_pix_key_type = request.form.get('payout_pix_key_type', 'random')

            if 'pix_test' in request.form:
                gross_amount = 5.00
            else:
                gross_amount = float(request.form['gross_amount'])
            
            if not payout_pix_key:
                flash('A chave Pix para saque é obrigatória.', 'error')
                return redirect(url_for('index'))

            if gross_amount < MINIMUM_VALUE and 'pix_test' not in request.form:
                flash(f'O valor mínimo da cobrança é R${MINIMUM_VALUE:.2f}.', 'error')
                return redirect(url_for('index'))
            
            commission = gross_amount * PERCENTAGE_COMMISSION
            total_commission = commission + FIXED_FEE
            net_amount = gross_amount - total_commission
            
            if net_amount <= 0:
                flash('O valor da cobrança é muito baixo e não cobre as taxas.', 'error')
                return redirect(url_for('index'))

            txid = str(uuid.uuid4())

            new_transaction = Transaction(
                txid=txid,
                net_amount=round(net_amount, 2),
                charge_amount=round(gross_amount, 2),
                payout_pix_key=payout_pix_key,
                payout_pix_key_type=payout_pix_key_type
            )
            db.session.add(new_transaction)
            db.session.commit()

            pix_code, qr_code_base64 = create_pix_charge(gross_amount, txid)

            if pix_code and qr_code_base64:
                return render_template('charge.html', pix_code=pix_code, qr_code_base64=qr_code_base64, charge_amount=gross_amount)
            else:
                flash('Não foi possível gerar a cobrança Pix no momento. Verifique os logs.', 'error')
                return redirect(url_for('index'))

        except (ValueError, TypeError):
            flash('Valor inválido. Por favor, insira um número.', 'error')
            return redirect(url_for('index'))

    return render_template('index.html', minimum_value=MINIMUM_VALUE)

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json()
    try:
        gross_amount = float(data.get('gross_amount', 0))
        commission = gross_amount * PERCENTAGE_COMMISSION
        total_commission = commission + FIXED_FEE
        net_amount = gross_amount - total_commission
        
        return jsonify({
            'commission': f'R$ {commission:.2f}',
            'fixed_fee': f'R$ {FIXED_FEE:.2f}',
            'net_amount': f'R$ {net_amount:.2f}' if net_amount > 0 else 'R$ 0.00'
        })
    except (ValueError, TypeError):
        return jsonify({'error': 'Valor inválido'}), 400

@app.route('/webhook', methods=['POST'])
def anubis_webhook():
    data = request.json
    print(f"Webhook recebido: {data}")
    if data.get("event") == "pix.charge.paid":
        charge_data = data.get("data", {})
        txid = charge_data.get("txid")
        transaction = Transaction.query.filter_by(txid=txid).first()
        if transaction and transaction.status == 'pending':
            transaction.status = 'paid'
            db.session.commit()
            print(f"Iniciando saque de R${transaction.net_amount} para a chave {transaction.payout_pix_key}")
            success, payout_data = send_pix_payout(transaction.net_amount, transaction.payout_pix_key, transaction.payout_pix_key_type)
            if success:
                transaction.status = 'withdrawn'
                print(f"Saque para txid {txid} realizado com sucesso.")
            else:
                transaction.status = 'payout_failed'
                print(f"Falha no saque para txid {txid}. Resposta da API: {payout_data}")
            db.session.commit()
    return "OK", 200

with app.app_context():
    db.create_all()
