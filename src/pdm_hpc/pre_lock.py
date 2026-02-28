from importlib.metadata import requires
from .utils import (
    fetch_package_metadata,
    get_external_deps,
    get_package_version,
    get_index_url,
)
from packaging.requirements import Requirement
from typing import Optional


def get_all_transitive_deps(
    package_name: str, version: str, index_url: str, visited: Optional[set[str]] = None
) -> set[str]:
    """Recursively get all transitive deps from PyPI metadata."""

    if visited is None:
        visited = set()
    if package_name.lower() in visited:
        return set()
    visited.add(package_name.lower())
    try:
        requires_dist = fetch_package_metadata(package_name.lower(), version, index_url)
    except Exception as e:
        print(
            f">>> WARNING: could not fetch PyPI metadata for {package_name}=={version}: {e}"
        )
        return set()

    result = set()
    for dep in requires_dist:
        try:
            from packaging.requirements import Requirement

            req = Requirement(dep)
        except Exception:
            continue

        if req.marker and "extra" in str(req.marker):
            continue

        if req.marker and not req.marker.evaluate():
            continue

        name = req.name.lower()
        if name not in visited:
            result.add(name)
            import urllib.request, json

            url = f"{index_url}/{name}/json"
            with urllib.request.urlopen(url) as response:
                dep_data = json.loads(response.read())
            dep_version = dep_data["info"]["version"]
            result.update(
                get_all_transitive_deps(name, dep_version, index_url, visited)
            )

    return result


def pin_found_or_error(project, **kwargs) -> None:
    external = get_external_deps(project)
    if not external:
        return

    resolution = project.pyproject.settings.setdefault("resolution", {})
    existing_overrides = dict(resolution.get("overrides", {}))
    existing_excludes = set(resolution.get("excludes", []))
    deps = project.pyproject.metadata.get("dependencies", [])
    index_url = get_index_url(project)
    errors = []
    requested = {}

    external_lower = {e.lower() for e in external}
    explicitly_requested = set()
    for dep in deps:
        req = Requirement(dep)
        name = req.name.lower()
        requested[name] = req.specifier
        if name not in external_lower:
            explicitly_requested.add(name)
    for package in external:
        requested_spec = requested.get(package.lower())
        if requested_spec is None:
            continue

        system_version = get_package_version(project, package)

        print(f">>> {package}:")
        print(f"      requested:  {requested_spec or 'any'}")
        print(f"      system:     {system_version or 'not found'}")

        if system_version is None:
            errors.append(f"  - {package}: not found in system Python")
            continue

        if requested_spec and not requested_spec.contains(system_version):
            errors.append(
                f"  - {package}: system has {system_version} "
                f"but {requested_spec} is required"
            )
            continue
        print(f"      OK: pinning {package}=={system_version}")

        existing_excludes.add(package.lower())
        existing_overrides[package] = system_version
        transitive = get_all_transitive_deps(
            package, system_version, index_url, visited=explicitly_requested
        )
        existing_excludes.update(transitive)

    if errors:
        raise RuntimeError(
            "\nExternal dependency validation failed:\n" + "\n".join(errors)
        )

    resolution["overrides"] = existing_overrides
    resolution["excludes"] = list(existing_excludes)
