# -*- coding: utf-8 -*-
from cheroot import wsgi
from wsgidav import __version__, util
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.wsgidav_app import WsgiDAVApp
import argparse
import logging
import worker  # Importing the worker module

def configure_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def create_app(html_path, root_path, allowed_countries, reverse_proxy_url, server_type, read_only):
    provider = FilesystemProvider(root_path, readonly=read_only)

    config = {
        "provider_mapping": {"/": provider},
        "simple_dc": {"user_mapping": {"*": True}},  # anonymous access
        "verbose": 3,
        "logging": {
            "enable": True,
            "enable_loggers": [],
        },
        "property_manager": True,
        "lock_storage": True,
    }

    app = WsgiDAVApp(config)
    headers = worker.load_headers(server_type)
    blocked_keywords = worker.load_blocked_keywords()
    
    def custom_app(environ, start_response):
        user_agent = environ.get('HTTP_USER_AGENT', '')
        ip = environ.get('REMOTE_ADDR', '')
        
        if worker.check_blocked_keywords(environ, blocked_keywords):
            if reverse_proxy_url:
                return worker.reverse_proxy(environ, start_response, reverse_proxy_url, headers)
            return worker.serve_html(environ, start_response, html_path, headers)
        
        if not worker.validate_ip(ip, allowed_countries):
            if reverse_proxy_url:
                return worker.reverse_proxy(environ, start_response, reverse_proxy_url, headers)
            return worker.serve_html(environ, start_response, html_path, headers)

        if worker.is_browser(user_agent) or worker.is_bot(user_agent):
            if environ['PATH_INFO'] == "/index.html":
                return worker.serve_html(environ, start_response, html_path, headers)
        return worker.serve_filesystem(environ, start_response, app, headers)

    return custom_app

def main():
    parser = argparse.ArgumentParser(description="Run a WebDAV server and serve an HTML page.")
    parser.add_argument('html_path', type=str, help="Path to the HTML file to serve")
    parser.add_argument('--host', type=str, default='0.0.0.0', help="Host to bind the server to")
    parser.add_argument('--port', type=int, default=8080, help="Port to bind the server to")
    parser.add_argument('--root', type=str, default='.', help="Root directory to serve files from")
    parser.add_argument('--allowed_countries', type=str, nargs='+', help="List of allowed country ISO codes")
    parser.add_argument('--reverse_proxy_url', type=str, help="URL to reverse proxy to instead of serving HTML")
    parser.add_argument('--server_type', type=str, choices=['nginx', 'netlify', 'cloudflare', 'apache', 'iis', 'aws_cloudfront', 'aws_lambda', 'google_cloud_function'], required=True, help="Type of server to mimic")
    parser.add_argument('--read_only', action='store_true', help="Make the file serve folder read-only")
    parser.add_argument('--log_file', type=str, default='server.log', help="Path to the log file")

    args = parser.parse_args()

    configure_logging(args.log_file)

    app = create_app(args.html_path, args.root, args.allowed_countries, args.reverse_proxy_url, args.server_type, args.read_only)

    server = wsgi.Server(
        bind_addr=(args.host, args.port),
        wsgi_app=app,
        server_name=f"WsgiDAV/{__version__} Cheroot/{wsgi.Server.version} Python/{util.PYTHON_VERSION}",
    )

    logging.info(f"Serving on http://{args.host}:{args.port}/ ...")
    logging.info(f"Serving files from {args.root}")
    if args.read_only:
        logging.info("Serving files in read-only mode")
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Received Ctrl-C: stopping...")
    finally:
        server.stop()

if __name__ == "__main__":
    main()