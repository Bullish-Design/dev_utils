import os
from collections import defaultdict
import ast
from typing import List, Tuple, Dict
import typer
from pathlib import Path
from rich import print

app = typer.Typer()


def extract_names(file_path: str) -> Tuple[List[str], List[str]]:
    """Extract class and function names from a Python file."""
    with open(file_path, "r") as file:
        try:
            tree = ast.parse(file.read())
        except SyntaxError:
            return [], []

    classes = []
    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_"):
                functions.append(node.name)

    return classes, functions


def get_relative_import_path(
    root_dir: Path, current_dir: Path, module_name: str = None
) -> str:
    """Generate the correct relative import path from root directory."""
    rel_path = current_dir.relative_to(root_dir)
    parts = list(rel_path.parts)
    if module_name:
        parts.append(module_name)
    return "." + ".".join(parts) if parts else "."


def process_directory(
    root_dir: Path, current_dir: Path
) -> Tuple[Dict[str, List[str]], List[str]]:
    """Process all Python files in directory including __init__.py files."""
    imports_by_module = defaultdict(list)
    all_names = []

    for item in current_dir.iterdir():
        if item.is_file() and item.suffix == ".py":
            if item.name == "__init__.py":
                classes, functions = extract_names(item)
                if (
                    current_dir != root_dir
                ):  # Skip root __init__.py to avoid circular imports
                    module_path = get_relative_import_path(root_dir, current_dir)
                    imports_by_module[module_path].extend(classes + functions)
                all_names.extend(classes + functions)
            else:
                module_name = item.stem
                classes, functions = extract_names(item)
                if classes or functions:
                    module_path = get_relative_import_path(
                        root_dir, current_dir, module_name
                    )
                    imports_by_module[module_path].extend(classes + functions)
                    all_names.extend(classes + functions)

        elif item.is_dir() and not item.name.startswith("."):
            sub_imports, sub_names = process_directory(root_dir, item)
            for module, names in sub_imports.items():
                imports_by_module[module].extend(names)
            all_names.extend(sub_names)

    return imports_by_module, all_names


@app.command()
def generate(
    directory: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=False,
        dir_okay=True,
        help="Directory to generate __init__.py for",
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-d", help="Print output without writing to file"
    ),
):
    """Generate __init__.py with imports for all Python files in directory."""
    imports_by_module, all_names = process_directory(directory, directory)

    # Remove duplicates while preserving order
    seen = set()
    all_names = [x for x in all_names if not (x in seen or seen.add(x))]

    # Generate import strings
    import_strings = []
    for module, names in sorted(imports_by_module.items()):
        # Remove duplicates while preserving order
        unique_names = []
        seen = set()
        for name in names:
            if name not in seen:
                unique_names.append(name)
                seen.add(name)
        if len(unique_names) == 1:
            import_strings.append(f"from {module} import {unique_names[0]}")
        else:
            import_strings.append(
                f"from {module} import (\n    {',\n    '.join(unique_names)},\n)"
            )

    output = "\n".join(import_strings) + "\n\n" + f"__all__ = {all_names}"

    if dry_run:
        print("[bold]Generated __init__.py content:[/bold]")
        print(output)
        return

    init_path = directory / "__init__.py"
    init_path.write_text(output)
    print(f"\n{output}\n")

    print(f"[green]Successfully generated: {init_path}[/green]\n")


if __name__ == "__main__":
    app()
