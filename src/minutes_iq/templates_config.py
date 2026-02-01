"""Templates configuration module to avoid circular imports."""

from pathlib import Path

from fastapi.templating import Jinja2Templates

# Set up templates path
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
