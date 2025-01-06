import typer
import tomlkit
from pathlib import Path
from enum import Enum


class BumpType(str, Enum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


app = typer.Typer()


def bump_version(current_version: str, bump_type: BumpType) -> str:
    major, minor, patch = map(int, current_version.split("."))

    if bump_type == BumpType.MAJOR:
        major += 1
        minor = patch = 0
    elif bump_type == BumpType.MINOR:
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    return f"{major}.{minor}.{patch}"


@app.command()
def bump(
    file_path: Path = typer.Argument(..., help="Path to pyproject.toml file"),
    bump_type: BumpType = typer.Option(
        BumpType.PATCH, help="Version part to bump: major, minor, or patch"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print the new version without modifying the file"
    ),
) -> None:
    """Bump the version in a pyproject.toml file."""

    if not file_path.exists():
        typer.echo(f"Error: File {file_path} not found", err=True)
        raise typer.Exit(1)

    content = tomlkit.loads(file_path.read_text())

    try:
        current_version = content["project"]["version"]
    except KeyError:
        typer.echo("Error: No version found in [project] section", err=True)
        raise typer.Exit(1)

    new_version = bump_version(current_version, bump_type)

    if dry_run:
        typer.echo(f"Current version: {current_version}")
        typer.echo(f"New version would be: {new_version}")
        return

    content["project"]["version"] = new_version
    file_path.write_text(tomlkit.dumps(content))
    typer.echo(f"Bumped version from {current_version} to {new_version}")


if __name__ == "__main__":
    app()
