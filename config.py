from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEFAULT_LIBRARY_PATH = DATA_DIR / "default_library.csv"

APP_TITLE = "Radar Orçamentário"
APP_SUBTITLE = (
    "Compare previsões orçamentárias padronizadas por tipo de gasto "
    "e destaque divergências com clareza."
)

MIN_COMPARISONS = 2
MAX_COMPARISONS = 4

SUPPORTED_FORECAST_EXTENSIONS = {"xlsx", "xlsm"}
SUPPORTED_LIBRARY_EXTENSIONS = {"xlsx", "xlsm", "csv"}
MAX_UPLOAD_SIZE_MB = 25

DEFAULT_THEME_COLOR = "#111111"
LIGHT_BACKGROUND = "#f3f3f3"
CARD_BACKGROUND = "#ffffff"
