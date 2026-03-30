# AgriTrak Deployment & Architecture

## Overview
AgriTrak is i s a web app which is flex-based, it's role is managing milk records for farmers and tracking their payments. The API used is [Open Exchange Rates API](https://www.exchangerate-api.com/) for converting currency. There were two webservers and a load balancer used in this project demonstrating a production deployment.

## Value Proposition
The Agritrak web app helps track milk production, amount earned and payment schedules woth real-time currency conversion to insure transparency in finances

## Architecture
- **Web-01:** 54.237.147.80 (Ubuntu, Flask app, Gunicorn, Nginx)
- **Web-02:** 13.221.238.172 (Ubuntu, Flask app, Gunicorn, Nginx)
- **lb01:** 98.93.185.230 (Ubuntu, HAProxy)

```
Client-> HAproxy lb->web01
                   |
                   ->web02   
```

## Key Files
- `app.py` — this is the main flax app
- `requirements.txt` — for python dependencies
- `data/users.json` — recording data
- `haproxy/haproxy.cfg` — HAproxy configuration
- `nginx/agritrack.conf` — nginx configuration
- `static/` and `templates/` — html and front end assets

## API Used
- **Currency Conversion:** [Open Exchange Rates API](https://www.exchangerate-api.com/)
  - Endpoint: `https://open.er-api.com/v6/latest/RWF`
  - Used for: converting from rwf to USD
  - Attribution: [Open Exchange Rates](https://www.exchangerate-api.com/)

## how to deploy

### 1. webservers (on both 54.237.147.80 and 13.221.238.172)
- Clone the repo 
- Set up Python environment (don't forget to install gunicorn)
- Run the app with Gunicorn:
  eg:
  nohup gunicorn --workers 4 --bind 127.0.0.1:5000 app:app > gunicorn.log 2>&1 &
- Configure Nginx to proxy requests to Gunicorn (try check `nginx/agritrack.conf`)

### 2. load Balancer (98.93.185.230)
- install HAProxy:
- Edit `/etc/haproxy/haproxy.cfg` (see `haproxy/haproxy.cfg` for example)
- restart HAprosy

## HAProxy Example Config
See `haproxy/haproxy.cfg` for example.

## updating Data
- To update users or records, edit `data/users.json` and copy it to both webservers.

## Testing & Load Balancing
- Access the app via the load balancer's IP or domain (e.g., http://98.93.185.230)
- Stop Gunicorn on one webserver and refresh to verify traffic is routed to the other
- to confirm round-robin balancing use browser dev tools.