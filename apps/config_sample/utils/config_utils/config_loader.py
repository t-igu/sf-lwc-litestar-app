from pathlib import Path
from .hot_config import HotConfig

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "config.toml"

config = HotConfig(path=CONFIG_PATH)
