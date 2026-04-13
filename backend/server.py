import uvicorn
import os
import sys

# Add the project root to sys.path to support absolute imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.config import get_config
from backend.logging_config import setup_logging_config

def main() -> None:
    setup_logging_config()
    uvicorn.run(
        "backend.interface.api.main:app",
        host=str(get_config("api.host", "0.0.0.0")),
        port=int(get_config("api.port", 8000)),
        reload=bool(get_config("api.reload", True)),
        log_level=str(get_config("logging.level", "info")).lower(),
        log_config=None,
    )

if __name__ == "__main__":
    main()
