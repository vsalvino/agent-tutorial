"""
A simple agent with command line and REST-ful web API.
"""


# ---- CORE FUNCTIONALITY ------------------------------------------------------


import random


def agent_phrase(randomize: bool = False) -> str:
    """
    Returns the agent's catch-phrase.
    """
    phrases = [
        "The name’s Bond. James Bond.",
        "Shaken, not stirred.",
        "They say you’re judged by the strength of your enemies.",
        "Problem solver? More of a problem eliminator.",
    ]
    if randomize:
        r_phrase = random.choice(phrases)
        return r_phrase
    else:
        return phrases[0]




# ---- WEB API -----------------------------------------------------------------


from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json


class WebApp(BaseHTTPRequestHandler):
    """
    A simple pure-python web app.
    """
    def do_GET(self):
        # Parse URL.
        parsed_url = urlparse(self.path)
        route: str = parsed_url.path
        query: dict = parse_qs(parsed_url.query)  # each entry is a list.

        # Response values.
        r_code: int = 200
        r_type: str = "application/json"
        r_content: str = ""

        try:
            # Phrase.
            if route == "/phrase":
                # Check the 'random' querystring.
                randomize: bool = query.get("random", [""])[0].lower() == "true"
                r_content = json.dumps({
                    "random": randomize,
                    "phrase": agent_phrase(randomize)
                })

            # Fallback, handle 404s.
            else:
                r_code = 404
                r_content = json.dumps({
                    "error": "No route found matching {}".format(route)
                })

            # Send the response.
            self.send_response(r_code)
            self.send_header("Content-Type", r_type)
            self.end_headers()
            self.wfile.write(r_content.encode("utf8"))

        # Handle server errors.
        except Exception as exc:
            self.send_error(500, message="Server Error.", explain=str(exc))




# ---- COMMAND LINE INTERFACE --------------------------------------------------


import argparse


def main() -> None:
    """
    Entrypoint into the command-line interface.
    """
    parser = argparse.ArgumentParser(
        description="A python server agent and CLI."
    )

    # Subparsers for sub-commands.
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # Phrase sub-command.
    phrase_help = "Prints a phrase."
    phrase_cli = subparsers.add_parser(
        name="phrase",
        description=phrase_help,
        help=phrase_help,
    )
    phrase_cli.add_argument(
        "--random",
        action="store_true",
        help="Print a random phrase each time."
    )

    # Webserver sub-command
    web_help = "Runs the built-in webserver."
    web_cli = subparsers.add_parser(
        name="webserver",
        description=web_help,
        help=web_help,
    )
    web_cli.add_argument(
        "--ssl_cert",
        type=str,
        default=None,
        help="Path to public SSL certificate file.",
    )
    web_cli.add_argument(
        "--ssl_key",
        type=str,
        default=None,
        help="Path to private SSL key file.",
    )

    # ---- Parse and route the sub-commands ------------------------------------

    args = parser.parse_args()

    # Phrase
    if args.command == "phrase":
        print(agent_phrase(args.random))

    # Webserver
    elif args.command == "webserver":
        try:
            from http.server import HTTPServer
            print("Running web server...")
            httpd = HTTPServer(("localhost", 8000), WebApp)
            if args.ssl_key and args.ssl_cert:
                import ssl
                httpd.socket = ssl.wrap_socket(
                    httpd.socket,
                    keyfile=args.ssl_key,
                    certfile=args.ssl_cert,
                    server_side=True
                )
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Bye.")


if __name__ == "__main__":
    main()
