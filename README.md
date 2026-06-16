# Foodora

A Django starter for a Foodora-style delivery platform.

## Structure

- `foodora/` contains the Django project configuration.
- `home/` contains the main app, admin registration, templates, and views.
- `static/` contains project static assets.
- `media/` stores uploaded files.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run `python manage.py migrate`.
4. Create a superuser with `python manage.py createsuperuser`.
5. Start the server with `python manage.py runserver`.
