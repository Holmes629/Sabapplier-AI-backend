# Sabapplier AI Backend

A Django-based REST API backend for the Sabapplier AI application with features including user authentication, Google OAuth, email OTP verification, document OCR, AI-powered form autofill, and cloud storage integration.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [API Keys & Third-Party Services](#api-keys--third-party-services)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Features

- 🔐 User Authentication (Email/Password & Google OAuth)
- 📧 Email OTP Verification
- 🔑 Forgot Password with OTP Reset
- 📄 OCR Document Processing
- 🤖 AI-Powered Form Autofill
- ☁️ Dropbox Cloud Storage Integration
- 🌐 CORS Support for Frontend Integration
- 📱 Browser Extension Support
- 🛡️ Secure File Upload Handling

## Tech Stack

- **Backend:** Django 5.1.7, Django REST Framework
- **Database:** SQLite (Development), PostgreSQL (Production)
- **AI/ML:** Google Generative AI (Gemini), Tesseract OCR
- **Cloud Storage:** Dropbox API
- **Authentication:** Google OAuth 2.0, JWT Tokens
- **Email:** SMTP (Gmail)
- **Image Processing:** OpenCV, Pillow, scikit-image
- **Document Processing:** pdf2image, python-docx

## Prerequisites

- Python 3.11+ 
- pip (Python package manager)
- Virtual environment (recommended)
- Gmail account for SMTP (or other email service)
- Google Cloud Console project for OAuth
- Dropbox Developer account
- Google AI API key

## Installation

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd Sabapplier-AI-backend
   ```

2. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment file:**
   ```bash
   cp .env.example .env  # Create from template or manually create .env
   ```

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Django Settings
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database Settings (for PostgreSQL production)
AIVEN_SERVICE_PASSWORD=your-postgresql-password

# Email Configuration (Gmail SMTP)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com

# Dropbox Configuration
DROPBOX_CLIENT_ID=your-dropbox-client-id
DROPBOX_CLIENT_SECRET=your-dropbox-client-secret
DROPBOX_REFRESH_TOKEN=your-dropbox-refresh-token

# Google AI Configuration
GOOGLE_AI_API_KEY=your-google-ai-api-key
```

## API Keys & Third-Party Services

### 1. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API and Google OAuth2 API
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Configure OAuth consent screen
6. Add authorized domains and redirect URIs:
   - `http://localhost:3000` (for development)
   - `https://yourdomain.com` (for production)
7. Copy the Client ID to your `.env` file

### 2. Gmail SMTP Setup

1. Enable 2-Factor Authentication on your Gmail account
2. Generate an App Password:
   - Go to Google Account Settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. Use your Gmail address as `EMAIL_HOST_USER`
4. Use the generated app password as `EMAIL_HOST_PASSWORD`

### 3. Dropbox API Setup

1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Create a new app with "Scoped access" type
3. Configure permissions:
   - `files.metadata.write`
   - `files.content.write` 
   - `files.content.read`
   - `sharing.write`
4. Generate OAuth2 tokens:
   ```bash
   # Use Dropbox OAuth2 flow to get refresh token
   # Or use their API explorer to generate tokens
   ```
5. Add Client ID, Client Secret, and Refresh Token to `.env`

### 4. Google AI (Gemini) API Setup

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add the API key to your `.env` file as `GOOGLE_AI_API_KEY`
4. The API is used for:
   - OCR text processing
   - Form autofill data generation

### 5. PostgreSQL Setup (Production)

For production deployment with Aiven PostgreSQL:

1. Sign up for [Aiven](https://aiven.io/)
2. Create a PostgreSQL service
3. Get connection details and update `DATABASES` in `settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql_psycopg2',
           'NAME': 'defaultdb',
           'USER': 'avnadmin',
           'PASSWORD': os.getenv('AIVEN_SERVICE_PASSWORD'),
           'HOST': 'your-host.aivencloud.com',
           'PORT': '24554',
       }
   }
   ```

## Database Setup

1. **Run migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

2. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

3. **Collect static files:**
   ```bash
   python manage.py collectstatic
   ```

## Running the Application

1. **Development server:**
   ```bash
   python manage.py runserver
   ```
   Server will be available at `http://127.0.0.1:8000/`

2. **Production server (with Gunicorn):**
   ```bash
   gunicorn backend.wsgi:application --bind 0.0.0.0:8000
   ```

3. **Using Uvicorn (ASGI):**
   ```bash
   uvicorn backend.asgi:application --host 0.0.0.0 --port 8000
   ```

## API Endpoints

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/register/` | User registration |
| POST | `/users/login/` | User login |
| POST | `/users/logout/` | User logout |
| GET | `/users/profile/` | Get user profile |
| POST | `/users/update/` | Update user data |
| POST | `/users/delete/` | Delete user account |

### OTP & Password Reset

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/send-otp/` | Send OTP to email |
| POST | `/users/verify-otp/` | Verify OTP code |
| POST | `/users/forgot-password/send-otp/` | Send password reset OTP |
| POST | `/users/forgot-password/reset/` | Reset password with OTP |

### Google OAuth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/google-signup/` | Google OAuth registration/login |

### Extension APIs

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/users/extension/login` | Extension-specific login |
| POST | `/users/extension/auto-fill/` | AI-powered form autofill |

### Example API Usage

```javascript
// Register new user
const response = await fetch('/users/register/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'securepassword123',
    fullName: 'John Doe'
  })
});

// Google OAuth Login
const googleResponse = await fetch('/users/google-signup/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    credential: 'google-jwt-token-here'
  })
});

// Auto-fill form data
const autofillResponse = await fetch('/users/extension/auto-fill/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    html_data: '<form>...</form>',
    user_email: 'user@example.com'
  })
});
```

## Deployment

### Environment-Specific Settings

1. **Production settings:**
   - Set `DEBUG=False`
   - Configure proper `ALLOWED_HOSTS`
   - Use PostgreSQL database
   - Set up proper CORS origins
   - Configure static file serving

2. **Docker Deployment:**
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   EXPOSE 8000
   CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000"]
   ```

3. **Heroku Deployment:**
   ```bash
   # Add Procfile
   echo "web: gunicorn backend.wsgi" > Procfile
   
   # Deploy
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

## Project Structure

```
Sabapplier-AI-backend/
├── backend/                 # Django project settings
│   ├── __init__.py
│   ├── asgi.py             # ASGI configuration
│   ├── settings.py         # Main settings file
│   ├── urls.py             # Root URL configuration
│   └── wsgi.py             # WSGI configuration
├── users/                   # Main application
│   ├── apis/               # API integrations
│   │   ├── fetch_autofill_data.py  # AI autofill logic
│   │   └── ocr_endpoint.py         # OCR processing
│   ├── migrations/         # Database migrations
│   ├── __init__.py
│   ├── admin.py           # Django admin configuration
│   ├── apps.py            # App configuration
│   ├── dropbox_storage.py # Dropbox storage backend
│   ├── models.py          # Database models
│   ├── serializers.py     # DRF serializers
│   ├── urls.py            # App URL patterns
│   └── views.py           # API views
├── media/                  # User uploaded files
├── staticfiles/           # Collected static files
├── db.sqlite3             # SQLite database (development)
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError for packages:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Database connection errors:**
   - Check PostgreSQL credentials
   - Ensure database server is running
   - Verify network connectivity

3. **Google OAuth errors:**
   - Verify Client ID in Google Console
   - Check authorized domains
   - Ensure proper redirect URIs

4. **Email sending failures:**
   - Verify Gmail app password
   - Check 2FA is enabled
   - Confirm SMTP settings

5. **Dropbox upload errors:**
   - Refresh Dropbox tokens
   - Check API permissions
   - Verify file paths

### Debug Mode

Enable detailed logging by adding to `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

## Security Considerations

1. **Never commit sensitive data:**
   - Use `.env` files for secrets
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. **API Security:**
   - Enable CORS only for trusted domains
   - Use HTTPS in production
   - Implement rate limiting
   - Validate all user inputs

3. **File Upload Security:**
   - Validate file types and sizes
   - Scan uploaded files
   - Use secure file storage

## Performance Optimization

1. **Database:**
   - Use connection pooling
   - Add database indexes
   - Optimize queries

2. **Caching:**
   - Implement Redis caching
   - Cache expensive API calls
   - Use browser caching for static files

3. **Media Files:**
   - Use CDN for static files
   - Compress images
   - Implement lazy loading

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation

---

**Note:** This project is under active development. Please check for updates regularly and follow the installation instructions carefully.
