import os
import subprocess
from libtmux import Server, Session, Window, Pane
import pynvim

from dev_utils.src.config import DEV_SOCKET_ENVVAR_NAME, NOTES_SOCKET_ENVVAR_NAME


# Get Tmux envvar by name:
def get_tmux_envvar(envvar_name):
    cmd_list = ["tmux", "showenv", envvar_name]
    output = subprocess.run(
        cmd_list,
        capture_output=True,
        text=True,
    )
    if output.returncode != 0:
        print(f"Error: {output.stderr}")
    else:
        tmux_var_string = output.stdout
        tmux_var_list = tmux_var_string.split("=")
        return tmux_var_list[1].strip()

    # return os.getenv(envvar_name)


# Set socket address for import
def print_tmux_envvars():
    output = get_tmux_envvar(DEV_SOCKET_ENVVAR_NAME)
    print(f"\nDev Envvar Output: {output}")

    output = get_tmux_envvar(NOTES_SOCKET_ENVVAR_NAME)
    print(f"\nNotes Envvar Output: {output}\n")


NVIM_SOCKET_DEV = get_tmux_envvar(DEV_SOCKET_ENVVAR_NAME)
NVIM_SOCKET_NOTES = get_tmux_envvar(NOTES_SOCKET_ENVVAR_NAME)
