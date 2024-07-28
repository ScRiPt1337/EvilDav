# -*- coding: utf-8 -*-
from cheroot import wsgi
from wsgidav import __version__, util
from wsgidav.fs_dav_provider import FilesystemProvider
from wsgidav.wsgidav_app import WsgiDAVApp
import argparse
import logging
import worker  # Importing the worker module
from colorama import init, Fore, Style

init()

BANNER = f"""
{Fore.RED}
▓█████ ██▒   █▓ ██▓ ██▓    ▓█████▄  ▄▄▄    ██▒   █▓
▓█   ▀▓██░   █▒▓██▒▓██▒    ▒██▀ ██▌▒████▄ ▓██░   █▒
▒███   ▓██  █▒░▒██▒▒██░    ░██   █▌▒██  ▀█▄▓██  █▒░
▒▓█  ▄  ▒██ █░░░██░▒██░    ░▓█▄   ▌░██▄▄▄▄██▒██ █░░
░▒████▒  ▒▀█░  ░██░░██████▒░▒████▓  ▓█   ▓██▒▒▀█░  
░░ ▒░ ░  ░ ▐░  ░▓  ░ ▒░▓  ░ ▒▒▓  ▒  ▒▒   ▓▒█░░ ▐░  
 ░ ░  ░  ░ ░░   ▒ ░░ ░ ▒  ░ ░ ▒  ▒   ▒   ▒▒ ░░ ░░  
   ░       ░░   ▒ ░  ░ ░    ░ ░  ░   ░   ▒     ░░  
   ░  ░     ░   ░      ░  ░   ░          ░  ░   ░  
           ░                ░                  ░   
{Style.RESET_ALL}
"""

def configure_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('EvilDav/1.0')

def print_banner():
    print(BANNER)
    print(f"{Fore.GREEN}EvilDav - WebDAV Server for Red Teaming{Style.RESET_ALL}")
    print(f"Version: 1.0")
    print(f"{Fore.BLUE}https://github.com/ScRiPt1337/EvilDav{Style.RESET_ALL}")
    print("\n")

def create_app(html_path, root_path, allowed_countries, blocked_countries, reverse_proxy_url, server_type, read_only, dav_url, allowed_user_agents, logger):
    provider = FilesystemProvider(root_path, readonly=read_only)

    config = {
        "provider_mapping": {dav_url: provider},
        "simple_dc": {"user_mapping": {"*": True}},  # anonymous access
        "verbose": 0,  # Set verbose to 0 to hide default output
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

        logger.info(f"Received request from IP: {ip}, User-Agent: {user_agent}")

        if not user_agent:
            logger.warning("User-Agent is missing. Blocking request by default.")
            return worker.serve_html(environ, start_response, html_path, headers)
        
        if worker.check_blocked_keywords(environ, blocked_keywords):
            if reverse_proxy_url:
                return worker.reverse_proxy(environ, start_response, reverse_proxy_url, headers)
            return worker.serve_html(environ, start_response, html_path, headers)
        
        if not worker.validate_ip(ip, allowed_countries, blocked_countries):
            if reverse_proxy_url:
                return worker.reverse_proxy(environ, start_response, reverse_proxy_url, headers)
            return worker.serve_html(environ, start_response, html_path, headers)

        if user_agent in allowed_user_agents:
            logger.info(f"Request identified as allowed user agent: {user_agent}")
            return worker.serve_filesystem(environ, start_response, app, headers)

        if worker.is_browser(user_agent):
            logger.info(f"Request identified as browser: {user_agent}")
            return worker.serve_html(environ, start_response, html_path, headers)

        if worker.is_bot(user_agent):
            logger.info(f"Request identified as bot: {user_agent}")
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
    parser.add_argument('--blocked_countries', type=str, nargs='+', help="List of blocked country ISO codes")
    parser.add_argument('--reverse_proxy_url', type=str, help="URL to reverse proxy to instead of serving HTML")
    parser.add_argument('--server_type', type=str, choices=['nginx', 'netlify', 'cloudflare', 'apache', 'iis', 'aws_cloudfront', 'aws_lambda', 'google_cloud_function'], required=True, help="Type of server to mimic")
    parser.add_argument('--read_only', action='store_true', help="Make the file serve folder read-only")
    parser.add_argument('--log_file', type=str, default='server.log', help="Path to the log file")
    parser.add_argument('--dav_url', type=str, default='/', help="URL path for WebDAV")
    parser.add_argument('--allowed_user_agents', type=str, nargs='+', help="List of allowed user agents")

    args = parser.parse_args()

    print_banner()

    if not args.allowed_countries:
        args.allowed_countries = []
        print(f"{Fore.YELLOW}Warning: No allowed countries set. Allowing all countries by default.{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}Allowed countries: {', '.join(args.allowed_countries)}{Style.RESET_ALL}")

    if not args.blocked_countries:
        args.blocked_countries = []
        print(f"{Fore.YELLOW}Warning: No blocked countries set. No country will be blocked.{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}Blocked countries: {', '.join(args.blocked_countries)}{Style.RESET_ALL}")

    if not args.reverse_proxy_url:
        print(f"{Fore.YELLOW}Warning: No reverse proxy URL set. Blocked requests will be served the HTML page.{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}Reverse proxy URL: {args.reverse_proxy_url}{Style.RESET_ALL}")

    if args.read_only:
        print(f"{Fore.GREEN}Serving files in read-only mode{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Serving files with write permissions{Style.RESET_ALL}")

    if not args.allowed_user_agents:
        args.allowed_user_agents = []
        print(f"{Fore.YELLOW}Warning: No allowed user agents set. All user agents will be processed normally.{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}Allowed user agents: {', '.join(args.allowed_user_agents)}{Style.RESET_ALL}")

    logger = configure_logging(args.log_file)

    app = create_app(args.html_path, args.root, args.allowed_countries, args.blocked_countries, args.reverse_proxy_url, args.server_type, args.read_only, args.dav_url, args.allowed_user_agents, logger)

    server = wsgi.Server(
        bind_addr=(args.host, args.port),
        wsgi_app=app,
        server_name=f"EvilDav/1.0 Cheroot/{wsgi.Server.version} Python/{util.PYTHON_VERSION}",
    )

    logger.info(f"Serving on http://{args.host}:{args.port}/ ...")
    logger.info(f"Serving files from {args.root} on {args.dav_url}")
    if args.read_only:
        logger.info("Serving files in read-only mode")
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("Received Ctrl-C: stopping...")
    finally:
        server.stop()

if __name__ == "__main__":
    main()