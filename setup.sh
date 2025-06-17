#!/bin/bash

# Sabapplier AI Backend Setup Script
# This script helps you set up the project quickly

echo "🚀 Setting up Sabapplier AI Backend..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

echo "✅ Python 3 found"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install core dependencies first
echo "📚 Installing core dependencies..."
pip install Django==5.1.7 djangorestframework==3.15.2 django-cors-headers==4.7.0 python-dotenv==1.1.0 psycopg2-binary==2.9.10 gunicorn==23.0.0 uvicorn==0.34.0 whitenoise==6.9.0 pillow requests

# Try to install remaining dependencies
echo "📦 Installing remaining dependencies..."
pip install -r requirements.txt --no-deps 2>/dev/null || echo "⚠️ Some packages may have conflicts. Core packages installed."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️ Please edit .env file with your actual API keys and configuration"
fi

# Run initial migrations
echo "🗃️ Running database migrations..."
python manage.py makemigrations
python manage.py migrate

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file with your API keys and configuration"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python manage.py runserver"
echo ""
echo "🌐 Server will be available at: http://127.0.0.1:8000/"
echo ""
echo "📖 See README.md for detailed configuration instructions"
