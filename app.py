from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask_marshmallow import Marshmallow
from joblib import load
import pandas as pd
import numpy as np


with open('new_best_model.joblib', 'rb') as f:
    best_model = load(f, mmap_mode=None)

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agromate.db')
app.config['JWT_SECRET_KEY'] = 'super-secret'
db = SQLAlchemy(app)
ma = Marshmallow(app)


@app.route('/')
def app_is_working():  # put application's code here
    return 'AgroMate is Online'


# Database

# Create Database
@app.cli.command('db_create')
def db_create():
    db.create_all()
    print("database created")


# Drop Database
@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print("database dropped")


# Add data to Database
@app.cli.command('db_seed')
def db_seed():
    farmer1 = Farmer(name = "123",
                     area = "0",
                     ph_number="119",
                     password = "123",
                     status="harvest")

    officer1 = AgriOfficer(name ="123",
                           ph_number="123",
                           password = "123"
                           )

    reseller1 = Reseller(name="123",
                     ph_number="119",
                     password="123",
                     economic_centre="dabulla")
    o2FProduction =O2FProduction(quantity='100',farmer_id='1')
    o2r = O2RResellDetail(reseller_id='1', quantity='1022', price='1313')

    db.session.add(officer1)
    db.session.add(farmer1)
    db.session.add(reseller1)
    db.session.add(o2FProduction)
    db.session.add(o2r)
    db.session.commit()
    print("database seeded")


# Data Models
class Farmer(db.Model):
    __tablename__ = "farmer"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    area = db.Column(db.String(120), nullable=False)
    ph_number = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(120), nullable = False)
    production = db.relationship('Production', backref='farmer', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AgriOfficer(db.Model):
    __tablename__ = "agriofficer"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    ph_number = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Reseller(db.Model):
    __tablename__ = "reseller"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    ph_number = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    economic_centre = db.Column(db.String(100), nullable=False)
    resellDetail = db.relationship('ResellDetail', backref='reseller', lazy=True)


    def __repr__(self):
        return f'<AgriOfficer {self.name}>'


class Production(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.id'), nullable=False)


class ResellDetail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    price = db.Column(db.String, nullable=True)
    reseller_id = db.Column(db.Integer, db.ForeignKey('reseller.id'), nullable=False)


class O2FProduction(db.Model):
    __tablename__ = "o2fproduction"
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Float, nullable=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.id'), nullable=False)


class O2RResellDetail(db.Model):
    __tablename__ = "o2rreselldetail"
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Float, nullable=True)
    price = db.Column(db.String, nullable=True)
    reseller_id = db.Column(db.Integer, db.ForeignKey('reseller.id'), nullable=False)


class ProductionSchema(ma.Schema):
    class Meta:
        fields = ('id', 'date', 'quantity')


class ResellDetailSchema(ma.Schema):
    class Meta:
        fields = ('id', 'date', 'quantity', 'price')


class FarmerSchema(ma.Schema):
    production = ma.Nested(ProductionSchema, many=True)
    class Meta:
        fields = ('id', 'name', 'area', 'status')

class ResellerSchema(ma.Schema):
    resellDetail = ma.Nested(ResellDetailSchema, many=True)
    class Meta:
        fields = ('id', 'date', 'quantity', 'price')


farmer_schema = FarmerSchema()
farmers_schema = FarmerSchema(many=True)

farmer_production = Production()
production_schema = ProductionSchema(many=True)
resellDetail_schema = ResellerSchema(many=True)


@app.route('/farmers', methods=['GET'])
def get_farmers():
    farmers = Farmer.query.all()
    farmer_schema = FarmerSchema()

    result = []
    for farmer in farmers:
        # Get the last production for this farmer
        last_production = Production.query.filter_by(farmer_id=farmer.id).order_by(Production.date.desc()).first()
        last_production_data = None
        if last_production:
            production_schema = ProductionSchema()
            last_production_data = production_schema.dump(last_production)

        # Serialize the farmer object with Marshmallow
        farmer_data = farmer_schema.dump(farmer)

        # Add the last production data to the serialized farmer object
        farmer_data['last_production'] = last_production_data

        # Add the serialized farmer object to the result list
        result.append(farmer_data)

    return jsonify(result)


@app.route('/o2fProduction/<farmer_id>', methods=['GET'])
def o2f_production(farmer_id):
    test = O2FProduction.query.filter_by(id=farmer_id).first()
    if test:
        quantity = test.quantity
        return jsonify({"quantity": quantity}), 201
    else:
        return jsonify(message="Error"), 401


@app.route('/production/<farmer_id>', methods=['GET'])
def production(farmer_id):
    production = Production.query.filter_by(farmer_id=farmer_id).all()
    result = production_schema.dump(production)
    test = Farmer.query.filter_by(id=farmer_id).first()
    if test:
        name = test.name
        return jsonify({"result": result, "name": name}), 201
    else:
        return jsonify(message="Farmer Login Succeeded!!")


@app.route('/farmer/<farmer_id>', methods=['GET'])
def farmer(farmer_id):
    farmer = Farmer.query.filter_by(id=farmer_id).first()
    #result = farmers_schema.dump(farmer)
    return jsonify(name=farmer.name, status=farmer.status), 200


# Farmer

# Farmer Registration
@app.route('/farmer/registration', methods=['POST'])
def farmer_registration():
    name = request.form['name']
    test = Farmer.query.filter_by(name=name).first()
    if test:
        return jsonify(message='That Name already exists.'), 409
    else:
        name = request.form['name']
        area = request.form['area']
        ph_number = request.form['ph_number']
        status = request.form['status']
        password = request.form['password']
        farmer = Farmer(name=name, area=area, ph_number=ph_number, status=status, password=password)
        db.session.add(farmer)
        db.session.commit()
        return jsonify(message='Registered'), 200


# Farmer Login
@app.route('/farmer/login', methods=['POST'])
def farmer_login():
    if request.is_json:
        name = request.json['name']
        password = request.json['password']
        print(name)
    else:
        name = request.form['name']
        password = request.form['password']
    test = Farmer.query.filter_by(name=name, password=password).first()
    if test:
        id = test.id
        return jsonify(message="Farmer Login Succeeded!!", id=id), 201
    else:
        return jsonify(message="Incorrect Username or Password"), 401


# Farmer Add his production weight
@app.route('/farmers/<int:farmer_id>/productions', methods=['POST'])
def add_production(farmer_id):
    farmer = Farmer.query.get_or_404(farmer_id)
    data = request.json
    date_str = data['date']
    quantity = data['quantity']
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format, use YYYY-MM-DD'}), 400
    production = Production(date=date, quantity=quantity, farmer=farmer)
    db.session.add(production)
    db.session.commit()

    return jsonify({'success': 'Production added successfully'}), 201


# Farmer Change his status
@app.route('/update_farmers_status/<int:farmer_id>', methods=['PUT'])
def update_farmer_status(farmer_id):
    # Get the request data
    new_status_body = request.get_json()
    new_status = new_status_body.get('status')
    test = Farmer.query.filter_by(id=farmer_id).first()
    print(new_status)

    if test:
        print()
        test = Farmer.query.get(farmer_id)
        test.status = new_status
        db.session.commit()
        return jsonify({'message': 'Farmer status updated successfully'})
    else:
        return jsonify({'error': 'Farmer not found'}), 404


# Agriculture Officer

# Agriculture Officer Login
@app.route('/agriofficer/login', methods=['POST'])
def agriofficer_login():
    if request.is_json:
        name = request.json['name']
        password = request.json['password']
    else:
        name = request.form['name']
        password = request.form['password']

    test = AgriOfficer.query.filter_by(name=name, password=password).first()
    if test:
        return jsonify(message="Officer Login Succeeded!!"), 201
    else:
        return jsonify(message="Incorrect userName or password"), 401


# Agriculture Officer Registration

@app.route('/agriofficer/registration', methods=['POST'])
def agriofficer_registration():
    name = request.form['name']
    test = AgriOfficer.query.filter_by(name=name).first()
    if test:
        return jsonify(message='That Name already exists.'), 409
    else:
        name = request.form['name']
        ph_number = request.form['ph_number']
        password = request.form['password']
        agriofficer = AgriOfficer(name=name, ph_number=ph_number, password=password)
        db.session.add(agriofficer)
        db.session.commit()
        return jsonify(message='Registered'), 201

@app.route('/o2f_production/add', methods=['POST'])
def add_o2f_production():
    if request.method == 'POST':
        # Parse the request data
        data = request.json
        quantity = data.get('quantity')
        farmer_id = data.get('farmer_id')

        # Check if the farmer exists
        farmer = Farmer.query.get(farmer_id)
        if not farmer:
            return jsonify({'error': 'Farmer not found'}), 404

        # Create a new O2FProduction instance
        o2f_production = O2FProduction(quantity=quantity, farmer_id=farmer_id)

        # Add the new instance to the session and commit
        db.session.add(o2f_production)
        db.session.commit()

        return jsonify({'message': 'Send successfully'}), 201
    else:
        return jsonify({'error': 'Invalid request method'}), 405


@app.route('/o2r_resell_detail/add', methods=['POST'])
def add_o2r_resell_detail():
    if request.method == 'POST':
        # Parse the request data
        data = request.json
        quantity = data.get('quantity')
        price = data.get('price')
        reseller_id = data.get('reseller_id')

        # Check if the reseller exists
        reseller = Reseller.query.get(reseller_id)
        if not reseller:
            return jsonify({'error': 'Reseller not found'}), 404

        # Create a new O2RResellDetail instance
        o2r_resell_detail = O2RResellDetail(quantity=quantity, price=price, reseller_id=reseller_id)

        # Add the new instance to the session and commit
        db.session.add(o2r_resell_detail)
        db.session.commit()

        return jsonify({'message': 'Send successfully '}), 201
    else:
        return jsonify({'error': 'Invalid request method'}), 405

# Reseller

# Reseller Login
@app.route('/reseller/login', methods=['POST'])
def reseller_login():
    if request.is_json:
        name = request.json['name']
        password = request.json['password']
    else:
        name = request.form['name']
        password = request.form['password']
    test = Reseller.query.filter_by(name=name, password=password).first()
    if test:
        id = test.id
        return jsonify(message="Reseller Login Succeeded!!", id=id), 201
    else:
        return jsonify(message="Incorrect Username or Password"), 401


# Reseller Registration

@app.route('/reseller/registration', methods=['POST'])
def reseller_registration():
    name = request.form['name']
    test = Reseller.query.filter_by(name=name).first()
    if test:
        return jsonify(message='That Name already exists.'), 401
    else:
        name = request.form['name']
        ph_number = request.form['ph_number']
        password = request.form['password']
        economic_centre = request.form['economic_centre']
        reseller = Reseller(name=name, ph_number=ph_number, password=password, economic_centre=economic_centre)
        db.session.add(reseller)
        db.session.commit()
        return jsonify(message='Registered'), 201


@app.route('/reseller/<int:reseller_id>/resellDetail', methods=['POST'])
def add_resell_detail(reseller_id):
    reseller = Reseller.query.get_or_404(reseller_id)
    data = request.json
    date_str = data['date']
    quantity = data['quantity']
    price = data['price']
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format, use YYYY-MM-DD'}), 400
    resellDetail = ResellDetail(date=date, quantity=quantity, reseller=reseller, price=price)
    db.session.add(resellDetail)
    db.session.commit()

    return jsonify({'success': 'Production added successfully'}), 201


@app.route('/reseller/reselldetail/<reseller_id>', methods=['GET'])
def resellDetail(reseller_id):
    resellDetail = ResellDetail.query.filter_by(reseller_id=reseller_id).all()
    result = resellDetail_schema.dump(resellDetail)
    test = Reseller.query.filter_by(id=reseller_id).first()
    if test:
        name = test.name
        return jsonify({"result": result, "name": name}), 201
    else:
        return jsonify(message="Reseller Login Succeeded!!")


@app.route('/o2r/<reseller_id>', methods=['GET'])
def O2R(reseller_id):
    test = O2RResellDetail.query.filter_by(reseller_id=reseller_id).order_by(O2RResellDetail.id.desc()).first()
    if test:
        quantity = test.quantity
        price = test.price
        return jsonify({"quantity": quantity, "price": price}), 201
    else:
        return jsonify(message="Error"), 401


@app.route('/predict', methods=['POST'])
def get_prediction():
    # Get data from the request
    data = request.get_json()
    date_to_test = data['date']  # Assuming 'date' is the key for the date input

    # Preprocess the input date
    timestamp_to_test = pd.to_datetime(date_to_test).timestamp()

    # Predict using the trained model
    forecast_result = best_model.predict(np.array([[timestamp_to_test]]))

    # Format the prediction result
    prediction = {
        "Ash_Plantain_LCVEG_1kg": forecast_result[0][0],
        "Production": forecast_result[0][1],
        "Resell_weight": forecast_result[0][2]
    }

    # Return the prediction as JSON
    return jsonify(prediction)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
