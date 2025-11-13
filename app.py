from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange


app = Flask(__name__)
app.secret_key = 'tajny_klic'  # pro session
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///eshop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Databázový model produktu
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())

# Validace formuláře pro přidání produktu
class ProductForm(FlaskForm):
    name = StringField('Název', validators=[DataRequired(), Length(min=2, max=100)])
    description = StringField('Popis', validators=[DataRequired(), Length(min=5, max=255)])
    price = IntegerField('Cena', validators=[DataRequired(), NumberRange(min=1)])
    type = SelectField('Typ', choices=[('notebook', 'Notebook'), ('sluchátka', 'Sluchátka'), ('myš', 'Myš')], validators=[DataRequired()])
    model = StringField('Model', validators=[DataRequired(), Length(min=2, max=50)])



@app.route('/', methods=['GET', 'POST'])
def index():
    form = ProductForm()
    selected_type = request.args.get('type', '')
    sort_order = request.args.get('sort', 'asc')
    # Získání typů z databáze
    types = sorted(set(p.type for p in Product.query.all()))
    # Filtrování produktů
    query = Product.query
    if selected_type:
        query = query.filter_by(type=selected_type)
    reverse = sort_order == 'desc'
    products = query.order_by(Product.price.desc() if reverse else Product.price.asc()).all()

    if form.validate_on_submit():
        new_product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            type=form.type.data,
            model=form.model.data
        )
        db.session.add(new_product)
        db.session.commit()
        flash('Produkt byl úspěšně přidán!', 'success')
        return redirect(url_for('index'))

    return render_template('index.html', products=products, types=types, selected_type=selected_type, sort_order=sort_order, form=form)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get(product_id)
    if not product:
        return 'Produkt nenalezen', 404
    return render_template('product.html', product=product)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get(product_id)
    if not product:
        return 'Produkt nenalezen', 404
    cart = session.get('cart', [])
    # Uloží pouze id produktu do košíku
    cart.append(product_id)
    session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', [])
    # Odstraní první výskyt id produktu
    if product_id in cart:
        cart.remove(product_id)
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart_ids = session.get('cart', [])
    products = Product.query.filter(Product.id.in_(cart_ids)).all() if cart_ids else []
    total = sum(product.price for product in products)
    return render_template('cart.html', cart=products, total=total)

def seed_products():
    if Product.query.count() == 0:
        default_products = [
            Product(name='Notebook Lenovo ThinkPad', description='Výkonný notebook pro práci i zábavu.', price=15000, type='notebook', model='ThinkPad X1'),
            Product(name='Notebook HP EliteBook', description='Spolehlivý notebook pro firemní použití.', price=13500, type='notebook', model='EliteBook 840'),
            Product(name='Sluchátka Sony WH-1000XM4', description='Bezdrátová sluchátka s dlouhou výdrží.', price=6500, type='sluchátka', model='WH-1000XM4'),
            Product(name='Sluchátka JBL Tune 510BT', description='Lehká sluchátka pro každodenní poslech.', price=1200, type='sluchátka', model='Tune 510BT'),
            Product(name='Myš Logitech MX Master 3', description='Ergonomická myš pro pohodlné ovládání.', price=2200, type='myš', model='MX Master 3'),
            Product(name='Myš Genius DX-110', description='Klasická drátová myš pro běžné použití.', price=250, type='myš', model='DX-110'),
        ]
        db.session.bulk_save_objects(default_products)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        seed_products()
    app.run(host='0.0.0.0', port=5000)
