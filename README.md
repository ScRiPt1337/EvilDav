
# EvilDav

EvilDav is a powerful and flexible WebDAV server with advanced features including geofencing, bot detection, keyword blocking, read-only mode, reverse proxy functionality, customizable server header mimicking, and logging.

## Features

- **Geofencing**: Restricts access based on the client's geographical location.
- **Bot Detection**: Detects and blocks bots based on user-agent strings.
- **Keyword Blocking**: Blocks requests containing specific keywords in headers or URLs.
- **Read-Only Mode**: Option to make the file serve folder read-only.
- **Reverse Proxy**: Option to forward blocked requests to another URL.
- **Server Header Mimicking**: Mimics headers from popular servers like NGINX, Netlify, Cloudflare, etc.
- **Logging**: Logs server activities to a specified file.

## Prerequisites

- Python 3.11
- Required Python packages:
  ```sh
  pip install -r requirements.txt
  ```

## Installation

Clone the repository:
```sh
git clone https://github.com/yourusername/evildav.git
cd evildav
```

## Configuration

### Blocked Keywords File

Create a file named `blocked_keywords.txt` with the following content:
```
blockedword1
blockedword2
blockedword3
```

### Server Headers Configuration

Create a file named `server_headers.json` with the following content:
```json
{
  "nginx": {
    "Server": "nginx",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block"
  },
  "netlify": {
    "Server": "Netlify",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block"
  },
  "cloudflare": {
    "Server": "cloudflare",
    "CF-RAY": "<ray-id>"
  },
  "apache": {
    "Server": "Apache"
  },
  "iis": {
    "Server": "Microsoft-IIS/10.0"
  },
  "aws_cloudfront": {
    "Server": "CloudFront",
    "X-Cache": "Miss from cloudfront"
  },
  "aws_lambda": {
    "Server": "awselb/2.0"
  },
  "google_cloud_function": {
    "Server": "Google Frontend"
  }
}
```

## Usage

Run the server with the following command:
```sh
python evildav.py /path/to/your/file.html --host 0.0.0.0 --port 8080 --root /path/to/serve --allowed_countries PK CN --reverse_proxy_url http://example.com --server_type nginx --read_only --log_file server.log
```

### Arguments

- `html_path`: Path to the HTML file to serve.
- `--host`: Host to bind the server to (default: `0.0.0.0`).
- `--port`: Port to bind the server to (default: `8080`).
- `--root`: Root directory to serve files from (default: `.`).
- `--allowed_countries`: List of allowed country ISO codes.
- `--reverse_proxy_url`: URL to reverse proxy to instead of serving HTML.
- `--server_type`: Type of server to mimic (choices: `nginx`, `netlify`, `cloudflare`, `apache`, `iis`, `aws_cloudfront`, `aws_lambda`, `google_cloud_function`).
- `--read_only`: Make the file serve folder read-only.
- `--log_file`: Path to the log file (default: `server.log`).

## Project Structure

```
evildav/
├── worker.py
├── wsgidav_server.py
├── server_headers.json
├── blocked_keywords.txt
├── README.md
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
