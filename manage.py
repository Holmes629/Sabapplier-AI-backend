#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)



def lambda_handler(event, context):
    from django.core.wsgi import get_wsgi_application
    from mangum import Mangum  # Mangum bridges ASGI apps to Lambda
    import os

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
    app = get_wsgi_application()
    handler = Mangum(app)
    return handler(event, context)


if __name__ == '__main__':
    main()
