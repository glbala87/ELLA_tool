import tempfile
import os
from typing import Callable


def test_export_classification(run_command: Callable):
    tmp = tempfile.NamedTemporaryFile()
    tmp.close()
    result = run_command(["export", "classifications", "--filename", tmp.name])
    assert result.exit_code == 0
    assert os.stat(tmp.name + ".xlsx").st_size > 0
    assert os.stat(tmp.name + ".csv").st_size > 0
