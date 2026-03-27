#!/usr/bin/env bash
# Usage: bash startup.sh
# Web server setup: Python, Flask, Gunicorn, NGINX

# Update and install dependencies
sudo apt update -y
sudo apt install -y python3-pip python3-venv nginx git

# Go to home directory
cd /home/ubuntu

# Clone repo if not already present
if [ ! -d "Playing_Around_with_APIs" ]; then
    git clone https://github.com/<YOUR_USERNAME>/Playing_Around_with_APIs.git
fi

cd Playing_Around_with_APIs

# Setup Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt gunicorn flask requests

# Run Flask app with Gunicorn on port 8000
nohup gunicorn -w 4 -b 0.0.0.0:8000 app:app > app.log 2>&1 &

# Configure NGINX
sudo rm -f /etc/nginx/sites-enabled/default
sudo cp nginx/agritrack.conf /etc/nginx/sites-available/agritrack
sudo ln -s /etc/nginx/sites-available/agritrack /etc/nginx/sites-enabled/agritrack
sudo nginx -t
sudo systemctl restart nginx

echo "AgriTrack setup complete on $(hostname)"