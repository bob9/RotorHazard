'''The release zip installs through RotorHazard's own plugin manager (install from file).'''
import filecmp
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_TESTS_DIR = os.path.dirname(os.path.realpath(__file__))
_PLUGIN_ROOT = os.path.dirname(_TESTS_DIR)
_REPO = os.path.dirname(_PLUGIN_ROOT)
sys.path.append(os.path.join(_REPO, 'src', 'server'))

from util.plugin_installation import PluginInstallationManager  # noqa: E402


def test_zip_installs_with_plugin_manager():
    out = tempfile.mkdtemp(prefix='rh_webapp_pkg_')
    subprocess.run(['bash', os.path.join(_PLUGIN_ROOT, 'package-plugin.sh'), out], check=True,
                   env=dict(os.environ, SKIP_BUILD='1'))
    zip_path = os.path.join(out, 'rh_webapp.zip')
    plugins_dir = Path(tempfile.mkdtemp(prefix='rh_webapp_plugins_'))
    manager = PluginInstallationManager(plugins_dir, {}, api_version='1.9', notify_cb=lambda msg: None)
    with open(zip_path, 'rb') as f:
        manager.install_from_upload(f.read())

    installed = plugins_dir / 'rh_webapp'
    source = Path(_PLUGIN_ROOT) / 'rh_webapp'
    assert sorted(p.name for p in plugins_dir.iterdir()) == ['rh_webapp']
    for rel in ('manifest.json', '__init__.py', 'compat.py', 'pages.py', 'translations.json',
                'static/classic.js', 'webapp/index.html'):
        assert filecmp.cmp(installed / rel, source / rel, shallow=False), rel
    expected = sorted(str(p.relative_to(source)) for p in source.rglob('*')
                      if p.is_file() and '__pycache__' not in p.parts)
    got = sorted(str(p.relative_to(installed)) for p in installed.rglob('*') if p.is_file())
    assert got == expected
