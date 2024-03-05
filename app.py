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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'agromate.db')  # Use SQLite as the database
app.config['JWT_SECRET_KEY'] = 'super-secret' # change this IRL
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

    db.session.add(officer1)
    db.session.add(farmer1)
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
    __tablename__ = "officer"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    ph_number = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<AgriOfficer {self.name}>'


class Production(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=True)
    quantity = db.Column(db.Float, nullable=True)
    farmer_id = db.Column(db.Integer, db.ForeignKey('farmer.id'), nullable=False)


class ProductionSchema(ma.Schema):
    class Meta:
        fields = ('id' ,'date', 'quantity')


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
@app.route('/register_farmer', methods=['POST'])
def register_farmer():
    data = request.get_json()
    print(data)
    name = data['name']
    area = data['area']
    password = data['password']
    ph_number = data['ph_number']
    status = data['status']

    # Check if farmer already exists in the database
    farmer = Farmer.query.filter_by(ph_number=ph_number).first()
    if farmer:
        return jsonify(message='Farmer already exists. Please choose a different name.', status='error'), 409
    else:
        # Create a new farmer
        new_farmer = Farmer(name=name, area=area, ph_number=ph_number, password=password, status=status)
        db.session.add(new_farmer)
        db.session.commit()
        return jsonify(message='Farmer registration successful! Please login.', status='success'), 200


# Farmer Login
@app.route('/farmerlogin', methods=['POST'])
def login():
    if request.is_json:
        name = request.json['name']
        password = request.json['password']
        print(name)
    else:
        name = request.form['name']
        password = request.form['password']
    test = Farmer.query.filter_by(name=name, password=password).first()
    if test:
        #access_token = create_access_token(indentity=name)
        id = test.id
        return jsonify(message="Farmer Login Succeeded!!", id=id), 200
    else:
        return jsonify(message="Incorrect userName or password"), 401


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
        # Update the status
        print()

        test = Farmer.query.get(farmer_id)
        test.status = new_status
        db.session.commit()

        return jsonify({'message': 'Farmer status updated successfully'})
    else:
        return jsonify({'error': 'Farmer not found'}), 404


# Agriculture Officer

# Agriculture Officer Login
@app.route('/agriofficerlogin', methods=['POST'])
def officer_login():
    if request.is_json:
        name = request.json['name']
        password = request.json['password']
        print(name)
    else:
        name = request.form['name']
        password = request.form['password']

    test = AgriOfficer.query.filter_by(name=name, password=password).first()
    if test:
        #access_token = create_access_token(indentity=name)
        return jsonify(message="Officer Login Succeeded!!"), 200
    else:
        return jsonify(message="Bad userName or password"), 401


# Agriculture Officer Registration
@app.route('/register_officer')
def register_officer():
    data = request.get_json()
    name = data['name']
    password = data['password']
    ph_number = data['ph_number']
    # Check if farmer already exists in the database
    officer = AgriOfficer.query.filter_by(ph_number=ph_number).first()
    if officer:
        return jsonify(message='Farmer already exists. Please choose a different name.', status='error'), 409
    else:
        # Create a new farmer
        new_officer = AgriOfficer(name=name, ph_number=ph_number, password=password)
        db.session.add(new_officer)
        db.session.commit()
        return jsonify(message='Farmer registration successful! Please login.', status='success'), 201


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
