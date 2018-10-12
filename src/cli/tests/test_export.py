import tempfile
import os


def test_export_classification(run_command):
    tmp = tempfile.NamedTemporaryFile()
    tmp.close()
    result = run_command(["export", "classifications", "--filename", tmp.name])
    assert result.exit_code == 0
    assert os.stat(tmp.name+".xlsx").st_size > 0
    assert os.stat(tmp.name+".csv").st_size > 0


def test_export_sanger(run_command):
    tmp = tempfile.NamedTemporaryFile()
    tmp.close()
    result = run_command(["export", "sanger", "testgroup01", "--filename", tmp.name])
    assert result.exit_code == 0
    assert os.stat(tmp.name+".xlsx").st_size > 0
    assert os.stat(tmp.name+".csv").st_size > 0

