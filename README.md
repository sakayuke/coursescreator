# Course Platform

Web platform for managing educational courses.

## Authors

- sakayuke
- Kana-Chan
- kelet1234
- lliibed
- patrykzajmala
- zacklol93

## Roles

- Admin
- Teacher
- Student

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-Login
- Microsoft SQL Server
- pyodbc
- FreeTDS
- Jinja2
- pytest

## Project Structure

```text
flask_learning/
├── app.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── decorators.py
│   ├── extensions.py
│   └── models.py
├── migrations/
├── templates/
├── static/
├── tests/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md





Setup
1. Clone the repository
git clone <repository-url>
cd coursescreator
2. Create a virtual environment
python -m venv venv

For Fish shell:

source venv/bin/activate.fish
3. Install dependencies
pip install -r requirements.txt
4. Configure environment

Copy the example environment file:

cp .env.example .env

Edit .env and configure your local SQL Server connection and secret key.

5. Create the database

Create a Microsoft SQL Server database named:

course_platform
6. Apply migrations
flask --app app.py db upgrade
7. Run the application
flask --app app.py run

The application will be available at:

http://127.0.0.1:5000
Git Workflow

Do not work directly in main.

Create a feature branch:

git checkout -b feature/your-feature

Make your changes and commit them:

git add .
git commit -m "Description of changes"

Push your branch:

git push -u origin feature/your-feature

Then create a Pull Request into main.

Important
Never commit .env.
Never commit passwords or secrets.
Do not force-push to main.
Do not delete another developer's migrations.
Pull the latest main before starting new work.
Keep main stable and use feature branches for development.
