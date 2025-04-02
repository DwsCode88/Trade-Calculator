from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///offers.db'
db = SQLAlchemy(app)


class Offer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    card_name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    cash_offer = db.Column(db.Float, nullable=False)
    trade_offer = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), default='Pending')
    # To store whether it's cash or trade
    accepted_type = db.Column(db.String(10), default=None)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            card_name = request.form['card_name']
            price = float(request.form['price'])
            cash_offer = round(price * 0.60, 2)  # 60% for cash
            trade_offer = round(price * 0.70, 2)  # 70% for trade
            new_offer = Offer(card_name=card_name, price=price,
                              cash_offer=cash_offer, trade_offer=trade_offer)
            db.session.add(new_offer)
            db.session.commit()
        except ValueError:
            return "Invalid input. Please enter a valid number.", 400

    offers = Offer.query.all()
    return render_template('index.html', offers=offers)


@app.route('/accept/<offer_type>/<int:offer_id>')
def accept_offer(offer_type, offer_id):
    offer = Offer.query.get(offer_id)
    if offer:
        if offer_type == 'cash':
            offer.accepted_type = 'Cash'
        elif offer_type == 'trade':
            offer.accepted_type = 'Trade'
        offer.status = 'Accepted'
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/deny/<int:offer_id>')
def deny_offer(offer_id):
    offer = Offer.query.get(offer_id)
    if offer:
        offer.status = 'Denied'
        db.session.commit()
    return redirect(url_for('index'))


@app.route('/clear')
def clear_all():
    Offer.query.delete()
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/accepted_trades')
def accepted_trades():
    # Get all accepted offers
    accepted_offers = Offer.query.filter_by(status='Accepted').all()

    # Calculate profit for each accepted offer
    total_profit = 0
    total_original_price = 0
    for offer in accepted_offers:
        # Calculate profit as the difference between the original price and accepted offer
        if offer.accepted_type == 'Cash':
            profit = offer.price - offer.cash_offer  # Original price minus cash offer
        elif offer.accepted_type == 'Trade':
            profit = offer.price - offer.trade_offer  # Original price minus trade offer

        # If profit is negative, set it to 0 to avoid negative profit
        if profit < 0:
            profit = 0

        total_profit += profit
        total_original_price += offer.price

    total_profit = round(total_profit, 2)  # Round total profit to 2 decimals
    # Round total original price to 2 decimals
    total_original_price = round(total_original_price, 2)

    return render_template('accepted_trades.html', offers=accepted_offers, total_profit=total_profit, total_original_price=total_original_price)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
