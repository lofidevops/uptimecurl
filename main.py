import datetime
import logging
import os
import socket

import chevron
import requests
from ruamel.yaml import YAML


def fail_on_exception(func):
    def _fail_on_exception(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.exception("An error occurred.")
            return False, str(e)

    return _fail_on_exception


def valid_read_filepath(path, descriptor="file"):

    path = os.path.abspath(path)
    if os.path.isfile(path) and os.access(path, os.R_OK):
        return path
    else:
        raise FileNotFoundError(f"Cannot read {descriptor} {path}")


def valid_write_filepath(path, descriptor="file"):

    path = os.path.abspath(path)
    base, filename = os.path.split(path)

    writeable_file = os.path.isfile(path) and os.access(path, os.W_OK)
    writeable_folder = (
        not os.path.exists(path) and os.path.isdir(base) and os.access(base, os.W_OK)
    )

    if writeable_file or writeable_folder:
        return path
    else:
        raise IOError(f"Cannot write {descriptor} {path}")


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


def execute(config_path, template_path, result_path):

    # validate paths (alert user early if invalid)
    config_path = valid_read_filepath(config_path, "configuration")
    template_path = valid_read_filepath(template_path, "template")
    result_path = valid_write_filepath(result_path, "results")

    # load configuration
    yaml = YAML()
    with open(config_path, "r") as configuration_file:
        config = yaml.load(configuration_file)

    # process
    data = process(config)

    base = os.path.basename(config_path)
    if base.endswith(".yaml"):
        base = base[:-5]

    data["title"] = base

    # write results
    with open(template_path, "r") as template:
        with open(result_path, "w") as result:
            result.write(chevron.render(template, data))


if __name__ == "__main__":
    execute("sample.yaml", "template.mustache", "result.html")
