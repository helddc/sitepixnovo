if request.method == 'POST':
    try:
        pix_test = 'pix_test' in request.form

        if pix_test:
            gross_amount = 5.00
        else:
            gross_amount = float(request.form['gross_amount'])
            if gross_amount < MINIMUM_VALUE:
                flash(f'O valor mínimo da cobrança é R${MINIMUM_VALUE:.2f}.', 'error')
                return redirect(url_for('index'))

        payout_pix_key = request.form['payout_pix_key']
        if not payout_pix_key:
            flash('A chave Pix para saque é obrigatória.', 'error')
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
            payout_pix_key=payout_pix_key
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
            flash('Não foi possível gerar a cobrança Pix no momento. Verifique os logs.', 'error')
            return redirect(url_for('index'))

    except (ValueError, TypeError):
        flash('Valor inválido. Por favor, insira um número.', 'error')
        return redirect(url_for('index'))
