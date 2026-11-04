"""Load ``.githooks/suite-gates.cfg``. A missing path is the default set."""

import configparser
from pathlib import Path


REJECT = 500
MAINTAIN = 200
AIM = 150
COGNITIVE = 15
MAX_ARGS = 5

_KEYS = (
    ("loc", "reject", REJECT),
    ("loc", "maintain", MAINTAIN),
    ("loc", "aim", AIM),
    ("complexity", "cognitive", COGNITIVE),
    ("complexity", "max_args", MAX_ARGS),
)


class ConfigError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message


class GateConfig:
    def __init__(self, reject, maintain, aim, cognitive, max_args, *, missing_file=False, missing_keys=None):
        self.reject = reject
        self.maintain = maintain
        self.aim = aim
        self.cognitive = cognitive
        self.max_args = max_args
        self.missing_file = missing_file
        self.missing_keys = list(missing_keys or [])


def missing_file_line():
    return (
        "suite-gates.cfg missing; using defaults "
        f"(reject {REJECT}, maintain {MAINTAIN}, aim {AIM}, "
        f"cognitive {COGNITIVE}, max_args {MAX_ARGS})."
    )


def missing_key_line(key, value):
    return f"suite-gates.cfg missing key {key}; using default {value}."


def _defaults():
    return GateConfig(REJECT, MAINTAIN, AIM, COGNITIVE, MAX_ARGS, missing_file=True)


def _constrain(values):
    reject = values["reject"]
    maintain = values["maintain"]
    aim = values["aim"]
    cognitive = values["cognitive"]
    max_args = values["max_args"]
    if reject <= 200:
        raise ConfigError(f"reject {reject} is not greater than 200")
    if not (reject > maintain > aim >= 0):
        raise ConfigError(
            f"need reject > maintain > aim >= 0, got {reject}, {maintain}, {aim}"
        )
    if cognitive < 0:
        raise ConfigError(f"cognitive {cognitive} is negative")
    if max_args < 0:
        raise ConfigError(f"max_args {max_args} is negative")


def load(path):
    """Return a GateConfig. A path that does not exist uses the defaults.

    A present file that is whitespace-only, unparsable, non-integral, or
    outside the constraints raises ConfigError. A missing key is not an error.
    """
    if path is None:
        return _defaults()
    path = Path(path)
    if not path.exists():
        return _defaults()
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ConfigError(str(exc)) from exc
    if raw.strip() == b"":
        raise ConfigError("whitespace-only")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ConfigError(f"unreadable ({exc.reason})") from exc
    if text.strip() == "":
        raise ConfigError("whitespace-only")
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(text)
    except configparser.Error as exc:
        raise ConfigError(" ".join(str(exc).split())) from exc
    values = {}
    missing = []
    for section, key, default in _KEYS:
        if not parser.has_section(section) or not parser.has_option(section, key):
            values[key] = default
            missing.append((key, default))
            continue
        raw_value = parser.get(section, key).strip()
        try:
            values[key] = int(raw_value)
        except ValueError as exc:
            raise ConfigError(f"{key} is not an integer") from exc
    _constrain(values)
    return GateConfig(
        values["reject"],
        values["maintain"],
        values["aim"],
        values["cognitive"],
        values["max_args"],
        missing_file=False,
        missing_keys=missing,
    )
