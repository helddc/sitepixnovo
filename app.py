# app.py (VERSÃO CORRIGIDA)
from flask import Flask, render_template, request, redirect, url_for, flash
import uuid
import os # <<< ESTA LINHA FOI ADICIONADA PARA CORRIGIR O ERRO

from config import FIXED_FEE, PERCENTAGE_COMMISSION, MINIMUM_VALUE
from database import db, Transaction
from anubis import create_pix_charge, send_pix_payout

app = Flask(__name__)
# Render usa uma variável de ambiente DATABASE_URL para bancos de dados.
# Se não estiver usando um DB do Render, ele cria um arquivo local.
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///transactions.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# A linha abaixo usa o 'os' para gerar uma chave segura
app.config['SECRET_KEY'] = os.urandom(24) 
db.init_app(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            net_amount = float(request.form['net_amount'])
            payout_pix_key = request.form['payout_pix_key']
            
            if not payout_pix_key:
                flash('A chave Pix para saque é obrigatória.', 'error')
                return redirect(url_for('index'))

            if net_amount < MINIMUM_VALUE:
                flash(f'O valor mínimo para receber é R${MINIMUM_VALUE:.2f}.', 'error')
                return redirect(url_for('index'))
            
            commission = net_amount * PERCENTAGE_COMMISSION
            total_charge = net_amount + commission + FIXED_FEE
            txid = str(uuid.uuid4())

            new_transaction = Transaction(
                txid=txid,
                net_amount=round(net_amount, 2),
                charge_amount=round(total_charge, 2),
                payout_pix_key=payout_pix_key
            )
            db.session.add(new_transaction)
            db.session.commit()

            pix_code, qr_code_base64 = create_pix_charge(total_charge, txid)

            if pix_code and qr_code_base64:
                return render_template(
                    'charge.html',
                    pix_code=pix_code,
                    qr_code_base64=qr_code_base64,
                    charge_amount=total_charge
                )
            else:
                flash('Não foi possível gerar a cobrança Pix no momento. Tente novamente.', 'error')
                return redirect(url_for('index'))

        except (ValueError, TypeError):
            flash('Valor inválido. Por favor, insira um número.', 'error')
            return redirect(url_for('index'))

    return render_template('index.html', minimum_value=MINIMUM_VALUE)

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
            success, payout_data = send_pix_payout(transaction.net_amount, transaction.payout_pix_key)
            
            if success:
                transaction.status = 'withdrawn'
                print(f"Saque para txid {txid} realizado com sucesso.")
            else:
                transaction.status = 'payout_failed'
                print(f"Falha no saque para txid {txid}. Resposta da API: {payout_data}")
            
            db.session.commit()

    return "OK", 200

# Este bloco cria o banco de dados na primeira vez que o app roda
with app.app_context():
    db.create_all()
