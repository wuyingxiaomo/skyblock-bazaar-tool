"""Runtime paths for source and PyInstaller builds."""

import os
import sys


SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = getattr(sys, "_MEIPASS", SOURCE_DIR) if getattr(sys, "frozen", False) else SOURCE_DIR

if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = SOURCE_DIR

DATA_DIR = os.path.join(BASE_DIR, "bazaar_config")


def ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def resource_path(*parts):
    return os.path.join(RESOURCE_DIR, *parts)


def data_path(*parts):
    return os.path.join(DATA_DIR, *parts)
