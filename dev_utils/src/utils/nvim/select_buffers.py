import typer
from pynvim import attach
from typing import List, Optional
import inquirer
from rich.console import Console
from rich.table import Table

from dev_utils.src.utils.nvim.nvim_init import NVIM_SOCKET_DEV, NVIM_SOCKET_NOTES

app = typer.Typer()
console = Console()


def get_nvim_instance():
    """Connect to Neovim instance."""
    try:
        return attach("socket", path=NVIM_SOCKET_DEV)
    except Exception as e:
        console.print(f"[red]Error connecting to Neovim: {e}[/red]")
        raise typer.Exit(1)


def get_buffer_list(nvim) -> List[dict]:
    """Get list of all buffers with their details."""
    buffers = []
    for buf in nvim.buffers:
        if buf.valid and buf.name:  # Only include valid buffers with names
            buffers.append(
                {
                    "number": buf.number,
                    "name": buf.name,
                    "modified": buf.options["modified"],
                }
            )
    return buffers


def display_buffers(buffers: List[dict]):
    """Display buffers in a formatted table."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Buffer #")
    table.add_column("File Path")
    table.add_column("Modified")

    for buf in buffers:
        modified = "[red]*[/red]" if buf["modified"] else ""
        table.add_row(str(buf["number"]), buf["name"], modified)

    console.print(table)


def select_buffers(buffers: List[dict], multiple: bool = True) -> List[str]:
    """Prompt user to select buffer(s)."""
    choices = [
        (
            f"{buf['number']}: {buf['name']}" + (" [*]" if buf["modified"] else ""),
            buf["name"],
        )
        for buf in buffers
    ]

    if multiple:
        questions = [
            inquirer.Checkbox(
                "selected",
                message="Select buffers (space to select, enter to confirm)",
                choices=choices,
            )
        ]
    else:
        questions = [
            inquirer.List("selected", message="Select a buffer", choices=choices)
        ]

    answers = inquirer.prompt(questions)
    if not answers:
        return []

    if multiple:
        return answers["selected"]
    return [answers["selected"]]


@app.command()
def list_buffers():
    """List all open Neovim buffers."""
    nvim = get_nvim_instance()
    buffers = get_buffer_list(nvim)
    display_buffers(buffers)


@app.command()
def select(
    multiple: bool = typer.Option(
        True, "--multiple", "-m", help="Allow multiple buffer selection"
    ),
) -> None:
    """Select one or more buffers and return their file paths."""
    nvim = get_nvim_instance()
    buffers = get_buffer_list(nvim)

    if not buffers:
        console.print("[yellow]No buffers found![/yellow]")
        raise typer.Exit(1)

    display_buffers(buffers)
    selected = select_buffers(buffers, multiple)

    if selected:
        for path in selected:
            print(path)
    else:
        console.print("[yellow]No buffers selected![/yellow]")


if __name__ == "__main__":
    app()
