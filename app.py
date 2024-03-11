from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask_marshmallow import Marshmallow
import joblib

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

    db.session.add(officer1)
    db.session.add(farmer1)
    db.session.add(reseller1)
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


    def __repr__(self):
        return f'<AgriOfficer {self.name}>'


class Production(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.id'), nullable=False)


class ProductionSchema(ma.Schema):
    class Meta:
        fields = ('id','date', 'quantity')


class FarmerSchema(ma.Schema):
    production = ma.Nested(ProductionSchema, many=True)
    class Meta:
        fields = ('id', 'name', 'area', 'status')


farmer_schema = FarmerSchema()
farmers_schema = FarmerSchema(many=True)

farmer_production = Production()
production_schema = ProductionSchema(many=True)


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


@app.route('/production/<farmer_id>', methods=['GET'])
def production(farmer_id):
    production = Production.query.filter_by(farmer_id=farmer_id).all()
    result = production_schema.dump(production)
    return jsonify(result)


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


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
