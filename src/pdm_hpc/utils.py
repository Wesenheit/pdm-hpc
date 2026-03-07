import subprocess
import re


def get_external_deps(project) -> list[str]:
    """Read [tool.pdm.external-dependencies] as a list of names."""
    return project.pyproject.settings.get("external-dependencies", {}).get(
        "packages", []
    )


def get_package_version(project, package_name: str) -> str | None:
    """Use the project's Python interpreter to detect version."""
    python = project.python.path

    result = subprocess.run(
        [
            str(python),
            "-c",
            f"from importlib.metadata import version; print(version('{package_name}'))",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()

    # fallback
    result = subprocess.run(
        [
            str(python),
            "-c",
            f"import {package_name.replace('-', '_')}; "
            f"print({package_name.replace('-', '_')}.__version__)",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return result.stdout.strip()

    return None


def get_package_deps_from_system(project, package_name: str) -> set[str]:
    """Get direct dependencies of a package from system Python metadata."""
    python = project.python.path

    result = subprocess.run(
        [
            str(python),
            "-c",
            f"""
from importlib.metadata import requires
import re
deps = requires('{package_name}') or []
for dep in deps:
    if 'extra ==' in dep:
        continue
    name = re.split(r'[>=<!;\\s\\[]', dep)[0].strip()
    if name:
        print(name)
""",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return set(result.stdout.strip().splitlines())
    return set()


def get_index_url(project) -> str:
    """Get the configured index URL from pyproject.toml or fall back to PyPI."""
    sources = project.pyproject.settings.get("source", [])
    for source in sources:
        if isinstance(source, dict):
            url = source.get("url", "")
            if url:
                return url.rstrip("/")
    return "https://pypi.org/pypi"


def fetch_package_metadata(
    package_name: str, version: str, index_url: str
) -> list[str]:
    import urllib.request
    import json

    url_to_try = f"{index_url}/{package_name}/{version}/json"
    try:
        with urllib.request.urlopen(url_to_try) as response:
            data = json.loads(response.read())
        requires_dist = data.get("info", {}).get("requires_dist") or []
        return requires_dist
    except Exception as e:
        print(
            f">>> WARNING: could not fetch metadata for {package_name}=={version}: {e}"
        )
        return []


def strip_version(version: str | None) -> str | None:
    if version is None:
        return None
    match = re.match(r"^(\d+\.\d+\.\d+)", version)

    if match:
        clean_version = match.group(1)
    else:
        clean_version = version

    return clean_version
