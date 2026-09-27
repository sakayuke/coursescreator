# Course Platform

Web platform for managing educational courses.

## Authors

* sakayuke
* Kana-Chan
* kelet1234
* lliibed
* patrykzajmala
* zacklol93

## Roles

* Admin
* Teacher
* Student

## Tech Stack

* Python
* Flask
* Flask-SQLAlchemy
* Flask-Migrate
* Flask-Login
* Microsoft SQL Server
* pyodbc
* FreeTDS
* Jinja2
* pytest

## Project Structure

```text
coursescreator/
├── run.py
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
```

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd coursescreator
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

For Fish shell:

```fish
source venv/bin/activate.fish
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and configure your local SQL Server connection and secret key.

### 5. Create the database

Create a Microsoft SQL Server database named:

```text
course_platform
```

### 6. Apply migrations

```fish
flask --app run:app db upgrade
```

### 7. Run the application

```fish
flask --app run:app run
```

The application will be available at:

```text
http://127.0.0.1:5000
```

## Validation, errors, and logs

All GET parameters are limited to 100 characters. Form fields are validated
against the limits of their corresponding model fields (including names,
titles, email addresses, passwords, and submitted content); email addresses
also receive format validation. The assignment list additionally validates the
`page` parameter as a positive integer. Invalid values return the 400 page
without changing application data. Existing status values and endpoints remain
unchanged; an unknown assignment status is treated as `all` and is recorded as
a warning for backwards compatibility.

Every HTTP request, rejected input, denied access, and HTTP error is written to
the server console. Set `LOG_LEVEL=DEBUG` in `.env` to include debug-level
messages.

## Tests

Run the automated tests with:

```bash
./venv/bin/pytest -q
```

## Git Workflow

Do not work directly in `main`.

Create a feature branch:

```bash
git checkout -b feature/your-feature
```

Make your changes and commit them:

```bash
git add .
git commit -m "Description of changes"
```

Push your branch:

```bash
git push -u origin feature/your-feature
```

Then create a Pull Request into `main`.

## Important

* Never commit `.env`.
* Never commit passwords or secrets.
* Do not force-push to `main`.
* Do not delete another developer's migrations.
* Pull the latest `main` before starting new work.
* Keep `main` stable and use feature branches for development.
