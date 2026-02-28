from importlib.metadata import requires
from .utils import get_external_deps, get_package_version
from packaging.requirements import Requirement


def pin_found_or_error(project, **kwargs) -> None:
    external = get_external_deps(project)
    if not external:
        return

    resolution = project.pyproject.settings.setdefault("resolution", {})
    existing_overrides = dict(resolution.get("overrides", {}))
    existing_excludes = set(resolution.get("excludes", []))
    deps = project.pyproject.metadata.get("dependencies", [])

    errors = []
    requested = {}
    for dep in deps:
        req = Requirement(dep)
        requested[req.name.lower()] = req.specifier

    for package in external:
        requested_spec = requested.get(package.lower())
        if requested_spec is None:
            continue
        existing_excludes.add(package)

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
        existing_overrides[package] = system_version

    if errors:
        raise RuntimeError(
            "\nExternal dependency validation failed:\n" + "\n".join(errors)
        )

    resolution["overrides"] = existing_overrides
    resolution["excludes"] = existing_excludes
