# AgriTrack Deployment & Architecture

## Overview
AgriTrack is a Flask-based web application for managing milk records, users, and payments. It uses the [Open Exchange Rates API](https://www.exchangerate-api.com/) for currency conversion. This project demonstrates a production deployment using two webservers and a load balancer (HAProxy).

## Value Proposition
AgriTrack helps farmers and managers track milk production, earnings, and payment schedules, with real-time currency conversion for financial transparency.

## Architecture
- **Webserver 1:** 54.237.147.80 (Ubuntu, Flask app, Gunicorn, Nginx)
- **Webserver 2:** 13.221.238.172 (Ubuntu, Flask app, Gunicorn, Nginx)
- **Load Balancer:** 98.93.185.230 (Ubuntu, HAProxy)

```
[Client]
   |
   v
[HAProxy Load Balancer]
   |         |
   v         v
[Webserver1] [Webserver2]
```

## Key Files
- `app.py` — Main Flask application
- `requirements.txt` — Python dependencies
- `data/users.json` — User and milk record data
- `haproxy/haproxy.cfg` — Example HAProxy config (with comments)
- `nginx/agritrack.conf` — Example Nginx config (if used)
- `static/` and `templates/` — Frontend assets and HTML templates

## API Used
- **Currency Conversion:** [Open Exchange Rates API](https://www.exchangerate-api.com/)
  - Endpoint: `https://open.er-api.com/v6/latest/RWF`
  - Used for: Converting RWF earnings to USD in the dashboard
  - Attribution: See [Open Exchange Rates](https://www.exchangerate-api.com/)

## Deployment Steps

### 1. Webservers (on both 54.237.147.80 and 13.221.238.172)
- Clone the repo:
  ```bash
  git clone https://github.com/YOUR_USERNAME/Playing_Around_with_APIs.git
  cd Playing_Around_with_APIs
  ```
- Set up Python environment:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
  pip install gunicorn
  ```
- Run the app with Gunicorn:
  ```bash
  nohup gunicorn --workers 4 --bind 127.0.0.1:5000 app:app > gunicorn.log 2>&1 &
  ```
- Configure Nginx to proxy requests to Gunicorn (see `nginx/agritrack.conf`)

### 2. Load Balancer (98.93.185.230)
- Install HAProxy:
  ```bash
  sudo apt update
  sudo apt install -y haproxy
  ```
- Edit `/etc/haproxy/haproxy.cfg` (see `haproxy/haproxy.cfg` for example)
- Restart HAProxy:
  ```bash
  sudo systemctl restart haproxy
  ```

## HAProxy Example Config
See `haproxy/haproxy.cfg` for a fully commented example.

## Updating Data
- To update users or records, edit `data/users.json` and copy it to both webservers.

## Testing & Load Balancing
- Access the app via the load balancer's IP or domain (e.g., http://98.93.185.230)
- Stop Gunicorn on one webserver and refresh to verify traffic is routed to the other
- Use browser dev tools or logs to confirm round-robin balancing

## Security & API Keys
- No sensitive API keys are required for the public currency API used.
- If you use a private API, store keys in a `.env` file and add `.env` to `.gitignore`.

## Error Handling
- The app displays user-friendly messages if the currency API is unavailable.
- All user input is validated on the frontend and backend.

## Useful Commands
- Check Gunicorn: `ps aux | grep gunicorn`
- Restart Gunicorn: `pkill gunicorn && nohup gunicorn --workers 4 --bind 127.0.0.1:5000 app:app > gunicorn.log 2>&1 &`
- Check Nginx: `sudo systemctl status nginx`
- Check HAProxy: `sudo systemctl status haproxy`

## Authors
- Kizito (and contributors)

---
For any issues, please open an issue on the repository or contact the maintainer.