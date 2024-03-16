AgroMate

AgroMate is an application built with Flask for managing agricultural data including farmer information, production data, and more.

Table of Contents

- Installation
- Usage
- Database Management
- Endpoints
- Contributing
- License

Installation

1. Clone the repository:

   git clone https://github.com/your_username/agromate.git

2. Navigate into the project directory:

   cd agromate

3. Install dependencies:

   pip install -r requirements.txt

Usage

1. Set up the Flask application:

   export FLASK_APP=app.py
   export FLASK_ENV=development

2. Initialize the database:

   flask db_create

3. Seed the database with initial data:

   flask db_seed

4. Run the application:

   flask run

Database Management

- To create the database tables:

  flask db_create

- To drop the database tables:

  flask db_drop

- To seed the database with initial data:

  flask db_seed

Endpoints

- GET /farmers: Get all farmers with their last production data.
- GET /o2fProduction/<farmer_id>: Get O2F production data for a specific farmer.
- GET /production/<farmer_id>: Get production data for a specific farmer.
- GET /farmer/<farmer_id>: Get details of a specific farmer.
- POST /farmer/registration: Register a new farmer.
- POST /farmer/login: Login as a farmer.
- POST /farmers/<farmer_id>/productions: Add production weight for a farmer.
- PUT /update_farmers_status/<farmer_id>: Update status of a farmer.
- POST /agriofficer/registration: Register a new agriculture officer.
- POST /agriofficer/login: Login as an agriculture officer.
- POST /reseller/registration: Register a new reseller.
- POST /reseller/login: Login as a reseller.

Contributing

Contributions are welcome! If you'd like to contribute to this project, please fork the repository and submit a pull request.

License

This project is licensed under the MIT License.
