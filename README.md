Building a Python Daemon & CLI
==============================

Did you ever wish to have a little python program running on your server to help
automate tasks? While a lot can be done with cron jobs, bash scripts, and
SSH-based tools such as ansible — sometimes having your own program waiting
and ready to do your bidding is exactly what you need.

In this article I will show you how to create a simple python agent that runs as
a system daemon and can be invoked via both command line and REST API.

Note: this code should be compatible with any version of Python 3.


First, create a CLI
-------------------

First I’m going to create a section for common app functionality. In this case,
it will just print a phrase.

```python
# ---- COMMON FUNCTIONALITY ----------------------------------------------------


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
```

Next, I’m going to create a CLI that can invoke my function.

Let’s to stick to the python standard library and use `argparse` to make a
simple command line interface.
The [python `argparse` docs](https://docs.python.org/3/library/argparse.html)
will give you a good introduction to how that works. I’m going to assume you’ve
read through that. My structure below is similar to the `argparse` tutorial and
uses sub-parsers to create nested commands.

```python
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
        description=phase_help,
        help=phrase_help,
    )
    phrase_cli.add_argument(
        "--random",
        action="store_true",
        help="Print a random phrase each time."
    )

    # ---- Parse and route the sub-commands ------------------------------------

    args = parser.parse_args()

    # Phrase
    if args.command == "phrase":
        print(agent_phrase(args.random))


if __name__ == "__main__":
    main()
```

Now if we invoke from the command line, it will print a phrase. Cool!

```console
$ python agent.py phrase --random
Shaken, not stirred.
```


Create a REST API
-----------------

Next we will expose our `agent_phrase` function over a RESTful web API.
I am going to do this in pure python, so that you can deploy this to any server
without having to worry about environments, pip packages, and the like.
For a more robust setup, you might want to do this using Bottle, Flask, or even
Django.

```python
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
                # Check the "random" querystring.
                random: bool = query.get("random", [""])[0].lower() == "true"
                r_content = json.dumps({
                    "random": random,
                    "phrase": agent_phrase(random=random)
                })

            # Fallback, handle 404s.
            else:
                r_code = 404
                r_content = json.dumps({
                    "error": "No route found matching {0}".format(route)
                })

            # Send the response.
            self.send_response(r_code)
            self.send_header("Content-Type", r_type)
            self.end_headers()
            self.wfile.write(r_content.encode("utf8"))

        # Handle server errors.
        except Exception as exc:
            self.send_error(500, message="Server Error.", explain=str(exc))
```

The last step remaining is to actually fire up a web server to serve our app.
I am going to stick to pure python once again and use the built-in `wsgiref`
server, which is intended for development or very basic production purposes.

To do that, I am going to add another sub-command to our CLI, `webserver_cli`
to invoke the web server.

```python
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
        description=phase_help,
        help=phrase_help,
    )
    phrase_cli.add_argument(
        "--random",
        action="store_true",
        help="Print a random phrase each time."
    )

    # Webserver sub-command
    webserver_help = "Runs the built-in webserver."
    webserver_cli = subparsers.add_parser(
        name="webserver",
        description=webserver_help,
        help=webserver_help,
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
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Bye.")


if __name__ == "__main__":
    main()
```

Now I can fire up the web server:

```console
$ python agent.py webserver
Running web server...
```

...and point my browser to `http://localhost:8000/phrase`. It’s alive! We can
also use the randomize option by adding a query string:
`http://localhost:8000/phrase?random=true`.


Adding SSL
----------

Just because we are using `wsgiref`, doesn’t mean we can’t also have security.
`wsgiref` is actually perfectly fine for internal-use-only services with
controlled traffic. Even though it is internal only, we would like our API to be
private and encrypted. It’s actually very simple to add an SSL certificate to
the built-in python webserver.

First, we need to issue a self-signed SSL certificate. I will let you peruse the
thousands upon thousands of other blog posts that tell you how to do that.
Windows users: if you have git installed, you also have OpenSSL!

With OpenSSL:

```console
$ openssl req -x509 -nodes -newkey rsa:2048 -keyout $HOME/key.pem -out $HOME/cert.pem -days 365
```

On Windows (with git installed):

```console
PS> & "C:\Program Files\Git\usr\bin\openssl.exe" req -x509 -nodes -newkey rsa:2048 -keyout $HOME\key.pem -out $HOME\cert.pem -days 365
```

Now that we have a private key (`key.pem`) and a public certificate
(`cert.pem`), we are ready to wire up SSL/TLS support on our webserver with just
a couple extra lines of code. Modify the `webserver_cli` and the
`if args.command == "webserver"` sub-command as so:

```python
# ---- COMMAND LINE INTERFACE --------------------------------------------------

    ....

    # Webserver sub-command
    webserver_help = "Runs the built-in webserver."
    webserver_cli = subparsers.add_parser(
        name="webserver",
        description=web_help,
        help=web_help,
    )
    webserver_cli.add_argument(
        "--ssl_cert",
        type=str,
        default=None,
        help="Path to public SSL certificate file.",
    )
    webserver_cli.add_argument(
        "--ssl_key",
        type=str,
        default=None,
        help="Path to private SSL key file.",
    )

    ....

    # Webserver
    elif args.command == "webserver":
        try:
            from http.server import HTTPServer
            print("Running web server...")
            httpd = HTTPServer(("localhost", 8000), WebApp)
            # Use SSL if keys were provided.
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
```

Now I can fire up the web server with SSL:

```console
$ python agent.py webserver --ssl_cert $HOME/cert.pem --ssl_key $HOME/key.pem
Running web server...
```

...and point my browser to `https://localhost:8000/phrase`. Then accept the
self-signed certificate warning in the browser.


Make Your Python Agent Web API into a Daemon
--------------------------------------------

While this might seem like the hard part, it is actually quite simple.
Unfortunately I have not yet done this part on Windows or Mac, so I will show
you how to do this on a Linux server with `systemd` (which is basically every
Linux system on earth at this point... but that’s a flame war for another day).

Create a file, `my-agent.service` with the correct paths to your python
executable (it could be in a virtual environment if so desired) and your
`agent.py` file as so:

```ini
[Unit]
Description=My python agent service

[Service]
ExecStart=/usr/bin/python3 /path/to/agent.py webserver
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Now run a couple OS commands (as root or using `sudo`) to install the service:

```bash
# copy config
$ cp my-agent.service /etc/systemd/system/

# reload configs
$ systemctl daemon-reload

# start the service
$ systemctl start cr-agent

# enable to start on reboot
$ systemctl enable cr-agent
```


That’s All, Folks
-----------------

Now you can explore the possibilities by replacing our simple `agent_phrase`
function with additional functionality that invokes sub-processes, writes to
files, or anything else you can imagine doing on a server. You could even have
the agents on two servers talk to each other via the REST API!

The full source code is available at:
https://github.com/vsalvino/agent-demo/blob/master/agent.py
