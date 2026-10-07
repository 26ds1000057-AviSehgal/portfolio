from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Layer 1: defaults (hardcoded)
DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# Layer 2: config.development.yaml (empty)
YAML_LAYER = {}

# Layer 3: .env file  (APP_ prefix stripped, NUM_WORKERS aliased to workers)
ENV_FILE = {
    "APP_PORT": "8345",
    "APP_LOG_LEVEL": "debug",
    "APP_API_KEY": "key-2yio6b0ks3",
}

# Layer 4: OS env vars (APP_ prefix)
OS_ENV = {
    "APP_DEBUG": "true",
    "APP_LOG_LEVEL": "debug",
    "APP_API_KEY": "key-xlvwm37zm0",
}

ALIASES = {"num_workers": "workers"}


def to_bool(v):
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "on")


def coerce(key, value):
    if key in ("port", "workers"):
        try:
            return int(str(value).strip())
        except ValueError:
            return value
    if key == "debug":
        return to_bool(value)
    return str(value)


def normalize(raw):
    """Strip APP_ prefix, lowercase, resolve aliases, coerce types."""
    out = {}
    for k, v in raw.items():
        name = k[4:] if k.upper().startswith("APP_") else k
        name = name.strip().lower()
        name = ALIASES.get(name, name)
        out[name] = coerce(name, v)
    return out


@app.get("/effective-config")
def effective_config(request: Request):
    cfg = dict(DEFAULTS)
    for layer in (YAML_LAYER, ENV_FILE, OS_ENV):
        cfg.update(normalize(layer))

    # Highest precedence: ?set=key=value (repeatable)
    for item in request.query_params.getlist("set"):
        if "=" not in item:
            continue
        k, _, v = item.partition("=")
        k = k.strip().lower()
        k = ALIASES.get(k, k)
        cfg[k] = coerce(k, v)

    cfg["api_key"] = "****"
    return cfg


@app.get("/")
def root():
    return {"ok": True, "endpoint": "/effective-config"}
