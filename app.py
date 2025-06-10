import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from config import FIXED_FEE, PERCENTAGE_COMMISSION, MINIMUM_VALUE
from anubis import create_pix_charge
from database import db, Transaction

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'padrao')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database.db')
db.init_app(app)

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            pix_test = 'pix_test' in request.form

            if pix_test:
                gross_amount = 5.00
            else:
                gross_amount = float(request.form['gross_amount'])
                if gross_amount < MINIMUM_VALUE:
                    flash(f'Valor mínimo é R${MINIMUM_VALUE:.2f}', 'error')
                    return redirect(url_for('index'))

            payout_pix_key = request.form['payout_pix_key']
            pix_key_type = request.form['pix_key_type']
            if not payout_pix_key:
                flash('Informe a chave Pix para saque', 'error')
                return redirect(url_for('index'))

            commission = gross_amount * PERCENTAGE_COMMISSION
            total_commission = commission + FIXED_FEE
            net_amount = gross_amount - total_commission

            if net_amount <= 0:
                flash('Valor não cobre as taxas.', 'error')
                return redirect(url_for('index'))

            txid = str(uuid.uuid4())
            new_transaction = Transaction(
                txid=txid,
                net_amount=round(net_amount, 2),
                charge_amount=round(gross_amount, 2),
                payout_pix_key=payout_pix_key,
                pix_key_type=pix_key_type
            )
            db.session.add(new_transaction)
            db.session.commit()

            pix_code, qr_code_base64 = create_pix_charge(gross_amount, txid)

            if pix_code and qr_code_base64:
                return render_template(
                    'charge.html',
                    pix_code=pix_code,
                    qr_code_base64=qr_code_base64,
                    charge_amount=gross_amount,
                    net_amount=net_amount,
                    total_commission=total_commission,
                    is_test=pix_test
                )
            else:
                flash('Erro ao gerar cobrança. Veja os logs.', 'error')
                return redirect(url_for('index'))

        except Exception as e:
            flash(f'Erro: {e}', 'error')
            return redirect(url_for('index'))
    return render_template('index.html')
