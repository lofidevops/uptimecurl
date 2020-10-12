# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright 2020 David Seaward and contributors


import datetime
import logging
import os
import socket

import chevron
import click
import requests
from dotenv import load_dotenv
from ruamel.yaml import YAML

LOCAL_FOLDER = os.path.dirname(__file__)
DEFAULT_CONFIG = os.path.join(LOCAL_FOLDER, "definition.yaml")
DEFAULT_TEMPLATE = os.path.join(LOCAL_FOLDER, "template.mustache")


def fail_on_exception(func):
    def _fail_on_exception(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception("An error occurred.")
            return False, str(e)

    return _fail_on_exception


@fail_on_exception
def http_ok(path):
    response = requests.head(path)
    status = response.status_code

    if status != requests.codes.ok:
        return False, f"{path} returned {status}"
    else:
        return True, None


@fail_on_exception
def port_ok(path, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((path, port))
    sock.close()

    if result != 0:
        return False, f"{path}:{port} returned {result}"
    else:
        return True, None


def process(tests):
    def _process(_tests):
        for name, settings in _tests.items():
            _type = settings["type"]
            timestamp = datetime.datetime.utcnow()

            if _type == "http_ok":
                url = settings["parameters"][0]
                success, message = http_ok(url)
            elif _type == "port_ok":
                server = settings["parameters"][0]
                port = settings["parameters"][1]
                success, message = port_ok(server, port)
            else:
                success, message = False, f"Test {_type} not recognised."

            yield {
                "name": name,
                "type": _type,
                "success_flag": success,
                "success_code": "💚" if success else "❌",
                "parameters": str(settings["parameters"]),
                "message": message,
                "timestamp": timestamp,
            }

    return {"data": list(_process(tests))}


def execute(definition_path, template_path, output_path):

    # load configuration
    yaml = YAML()
    with open(definition_path, "r") as definition_file:
        monitor = yaml.load(definition_file)

    # process
    results = process(monitor)

    base = os.path.basename(definition_path)
    if base.endswith(".yaml"):
        base = base[:-5]

    results["title"] = base

    # write results
    with open(template_path, "r") as template:
        with open(output_path, "w") as output_file:
            output_file.write(chevron.render(template, results))


@click.command()
@click.option(
    "--definition",
    default=DEFAULT_CONFIG,
    envvar="UPTIMECURL_DEFINITION",
    help="List of test definitions (YAML).",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
)
@click.option(
    "--template",
    default=DEFAULT_TEMPLATE,
    envvar="UPTIMECURL_TEMPLATE",
    help="Template to generate report from test results (Mustache).",
    type=click.Path(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        resolve_path=True,
    ),
)
@click.option(
    "--output",
    default="./result.html",
    envvar="UPTIMECURL_OUTPUT",
    help="Output path for report (typically HTML).",
    type=click.Path(
        exists=False,  # MAY exist
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
    ),
)
def cli(definition, template, output):
    """
    Basic monitoring tool designed for rapid deployment and simple results.

    Define tests in the DEFINITION file and template in the TEMPLATE file.
    Report is generated at the OUTPUT path.

    Instead of command-line parameters you can use the environment
    variables UPTIMECURL_DEFINITION, UPTIMECURL_TEMPLATE and
    UPTIMECURL_OUTPUT. These can be defined in a .env file in the working
    directory.
    """

    load_dotenv()
    execute(definition, template, output)
