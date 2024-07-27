import requests
import json
import logging

# Initialize logging
logger = logging.getLogger('WebDAVServer')
logger.setLevel(logging.INFO)

def load_headers(server_type):
    with open('server_headers.json', 'r') as file:
        headers_config = json.load(file)
    return [(k, v) for k, v in headers_config.get(server_type, {}).items()]

def load_blocked_keywords():
    with open('blocked_keywords.txt', 'r') as file:
        return [line.strip() for line in file]

def is_browser(user_agent):
    return any(keyword in user_agent.lower() for keyword in ['mozilla', 'chrome', 'safari'])

def is_bot(user_agent):
    bots = ['bot', 'crawler', 'spider', 'shodan', 'scanner']
    return any(bot in user_agent.lower() for bot in bots)

def get_country(ip):
    url = f"http://ip-api.com/json/{ip}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data.get('countryCode')
    logger.warning(f"Failed to get country for IP: {ip}")
    return None

def serve_html(environ, start_response, html_path, headers):
    with open(html_path, 'r') as f:
        html_content = f.read()
    headers.append(('Content-Type', 'text/html'))  # Ensure Content-Type is set to text/html
    start_response('200 OK', headers)
    logger.info("Serving HTML page.")
    return [html_content.encode('utf-8')]

def serve_filesystem(environ, start_response, app, headers):
    environ['start_response_headers'] = headers
    logger.info("Serving filesystem content.")
    return app(environ, start_response)

def validate_ip(ip, allowed_countries):
    country = get_country(ip)
    if country in allowed_countries:
        logger.info(f"IP {ip} is allowed.")
        return True
    logger.warning(f"IP {ip} is not allowed.")
    return False

def check_blocked_keywords(environ, blocked_keywords):
    for key, value in environ.items():
        if any(keyword in str(value).lower() for keyword in blocked_keywords):
            logger.warning(f"Blocked keyword found in {key}: {value}")
            return True
    return False

def reverse_proxy(environ, start_response, target_url, headers):
    path = environ['PATH_INFO']
    query = environ['QUERY_STRING']
    url = f"{target_url}{path}?{query}" if query else f"{target_url}{path}"
    request_headers = {key[5:]: value for key, value in environ.items() if key.startswith('HTTP_')}
    request_headers['Host'] = target_url.split('//')[1].split('/')[0]
    response = requests.request(
        method=environ['REQUEST_METHOD'],
        url=url,
        headers=request_headers,
        data=environ['wsgi.input'].read(int(environ.get('CONTENT_LENGTH', 0)) or None)
    )
    start_response(f'{response.status_code} {response.reason}', list(response.headers.items()))
    logger.info(f"Reverse proxy to {url} with status {response.status_code}.")
    return [response.content]