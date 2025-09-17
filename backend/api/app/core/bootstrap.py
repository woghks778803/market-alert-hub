import importlib, pkgutil

def load_market_adapters() -> None:
    import app.api.adapters.market as pkg
    for m in pkgutil.iter_modules(pkg.__path__):
        importlib.import_module(f"{pkg.__name__}.{m.name}")
