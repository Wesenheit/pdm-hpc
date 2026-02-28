import subprocess


def get_external_deps(project) -> list[str]:
    """Read [tool.pdm.external-dependencies] as a list of names."""
    return project.pyproject.settings.get("external-dependencies", {}).get(
        "packages", []
    )


def get_package_version(project, package_name: str) -> str | None:
    """Use the project's Python interpreter to detect version."""
    python = project.python.path  # gets the project's configured python path

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
