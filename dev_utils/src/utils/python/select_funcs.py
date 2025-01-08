import ast
import typer
from typing import Dict, List, Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich import print as rprint
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import json

app = typer.Typer()
console = Console()


def extract_functions(filepath: str) -> List[Dict]:
    """
    Extract all function definitions from a Python file.
    Returns a list of dictionaries containing function details.
    """
    with open(filepath, "r") as file:
        tree = ast.parse(file.read())

    functions = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(
                {"name": node.name, "lineno": node.lineno, "filepath": filepath}
            )

    return functions


def display_functions(functions: List[Dict]) -> None:
    """Display the list of functions in a formatted table."""
    table = Table(show_header=True)
    table.add_column("Index", style="cyan")
    table.add_column("Function Name", style="green")
    table.add_column("Line Number", style="yellow")

    for idx, func in enumerate(functions, 1):
        table.add_row(str(idx), func["name"], str(func["lineno"]))

    console.print(table)


def get_user_selection(functions: List[Dict]) -> List[int]:
    """
    Get user selection of functions using prompt_toolkit.
    Returns a list of selected indices.
    """
    # Create a completer with valid indices
    valid_indices = [str(i) for i in range(1, len(functions) + 1)]
    completer = WordCompleter(valid_indices)

    while True:
        rprint(
            "[yellow]Enter function indices separated by spaces (e.g., '1 3 4')[/yellow]"
        )
        selection = prompt("Selection: ", completer=completer).strip()

        try:
            # Convert input to list of integers
            indices = [int(idx) for idx in selection.split()]

            # Validate indices
            if all(1 <= idx <= len(functions) for idx in indices):
                return indices
            else:
                rprint("[red]Invalid selection. Please enter valid indices.[/red]")
        except ValueError:
            rprint(
                "[red]Invalid input. Please enter numbers separated by spaces.[/red]"
            )


@app.command()
def select_functions(
    filepath: str = typer.Argument(..., help="Path to the Python file"),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output JSON file path"
    ),
) -> None:
    """
    List all functions in a Python file and allow multi-selection.
    Returns a dictionary of filepath and function names for selected functions.
    """
    # Validate file path
    if not Path(filepath).exists() or not filepath.endswith(".py"):
        rprint("[red]Error: Invalid Python file path[/red]")
        raise typer.Exit(1)

    # Extract functions
    functions = extract_functions(filepath)

    if not functions:
        rprint("[yellow]No functions found in the file.[/yellow]")
        raise typer.Exit(0)

    # Display functions
    display_functions(functions)

    # Get user selection
    selected_indices = get_user_selection(functions)

    # Create result dictionary
    result = {
        "filepath": filepath,
        "selected_functions": [
            {"name": functions[idx - 1]["name"], "lineno": functions[idx - 1]["lineno"]}
            for idx in selected_indices
        ],
    }

    # Output results
    if output:
        with open(output, "w") as f:
            json.dump(result, f, indent=2)
        rprint(f"[green]Results saved to {output}[/green]")
    else:
        rprint(result)


if __name__ == "__main__":
    app()
