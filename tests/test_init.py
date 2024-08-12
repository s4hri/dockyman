import os
import shutil
import tempfile
import pytest
from click.testing import CliRunner
from dockyman.cli import cli


# Fixture to create and clean up a temporary directory for testing
@pytest.fixture
def temp_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

# Helper function to get all files in the templates directory
def get_template_files(template_dir):
    files = []
    for root, dirs, filenames in os.walk(template_dir):
        for filename in filenames:
            relative_path = os.path.relpath(os.path.join(root, filename), template_dir)
            files.append(relative_path)
    return files

# Test for the init command
def test_init_command(temp_dir):
    # Get the path to the model directory
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'dockyman', 'model')
    
    # Get the list of template files
    template_files = get_template_files(template_dir)

    runner = CliRunner()
    result = runner.invoke(cli, ['init', temp_dir])

    # Assert the command was successful
    assert result.exit_code == 0
    # Assert the target directory exists
    assert os.path.exists(temp_dir)
    
    # Assert each template file was copied to the target directory
    for template_file in template_files:
        target_file = os.path.join(temp_dir, template_file)
        assert os.path.exists(target_file)
    
    # Assert the output contains the expected message
    assert "Dockyman template files copied with ownership changed" in result.output
