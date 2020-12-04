import os
from pathlib import Path


def get_attachments(analysis_name):
    if "ANALYSES_PATH" not in os.environ:
        return []
    folder = Path(os.environ["ANALYSES_PATH"]) / analysis_name / "attachments"
    if folder.exists():
        files = sorted(list(folder.glob("*")))
    else:
        files = []

    return files
