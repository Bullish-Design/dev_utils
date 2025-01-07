from libtmux import Server, Session, Window, Pane
import os
import subprocess
import argparse
from typing import List, Dict
from dataclasses import dataclass
from pydantic import BaseModel


class TmuxBase(BaseModel):
    """Base class for tmux objects"""

    class Config:
        arbitrary_types_allowed = True


class SessionActivity(TmuxBase):
    session_obj: Session
    name: str
    started: int
    activity: int
    created: int
    last_attached: int
    window_activity: int


SessionActivity.model_rebuild()


class WindowActivity(TmuxBase):
    window_obj: Window
    name: str
    activity: int
    created: int
    last_attached: int
    pane_activity: int


WindowActivity.model_rebuild()


def print_class_dict(class_obj):
    print(f"\nPrinting Class Dict for: {class_obj}")
    for key, val in class_obj.__dict__.items():
        print(f"   {key}: {val}")
    print(f"\n\n")


def get_current_session(server: Server):
    session_activity = []
    # print(f"\n\nPrinting Server Sessions:\n")
    for session in server.sessions:
        # print(f"\n\nSession: {session}")
        session_data = SessionActivity(
            session_obj=session,
            name=session.session_name,
            started=session.start_time,
            activity=session.session_activity,
            created=session.session_created,
            last_attached=session.session_last_attached,
            window_activity=session.window_activity,
        )
        session_activity.append(session_data)

    latest_active_sesh = (None, 0)
    for sesh in session_activity:
        # print(
        #    f"Session {sesh.name:<7} = Activity: {sesh.activity} | Created: {sesh.created} | Last Attached: {sesh.last_attached} | Window Activity: {sesh.window_activity}"
        # )
        if int(sesh.activity) > int(latest_active_sesh[1]):
            # print(f"  Setting latest active session to: {sesh.name}")
            latest_active_sesh = (sesh, sesh.activity)
    # print(f"\nLatest Active Session: {latest_active_sesh[0].name}\n")
    return latest_active_sesh[0].session_obj


def get_current_window(session: Session):
    active_windows = []
    for window in session.windows:
        pass


def compare_objects(obj_list: List):
    different_attrs = []
    attr_list = obj_list[0].__dir__()
    # print(f"\n\n{attr_list}\n\n")
    current_key = None
    # for obj in obj_list:
    print(f"\nComparing Attributes:")
    for attr in attr_list:
        if attr.startswith("__"):
            break
        current_attr_vals = []
        for obj in obj_list:
            current_attr_vals.append(getattr(obj, attr))

        # print(current_attr_vals)
        print(f"    {attr}: {current_attr_vals}")
        # if not len(set(current_attr_vals)) <= 1:
        #    different_attrs.append(attr)
    return different_attrs


def set_nvim_active_file_env_var(
    pane: Pane, env_var: str, value: str = "vim.fn.expand('%:p')"
):
    lua_file_path_str = f"lua vim.env.{env_var} = string.format('%s', {value})"
    output = send_command_back_to_tmux(pane, lua_file_path_str)
    return output


def send_command_back_to_tmux(pane: Pane, command: str):
    #    #command = lua_file_path_str
    build_command = f":{command}"
    session = "System"  # pane.session  # .session_name
    window = "Dev Utils"  # pane.window  # .name
    pane_name = 2

    tmux_args = f"{session}:{window}.{pane_name}"
    # output = pane.send_keys(command, enter=True)
    # print(f"Output: {output}")

    # output = subprocess.run(
    #    [build_command],
    #    capture_output=True,
    #    text=True,
    # )

    output = subprocess.run(
        ["tmux", "send-keys", "-t", tmux_args, build_command, "Enter"],
        capture_output=True,
        text=True,
    )
    return output


def set_tmux_env_var_from_nvim(
    pane: Pane, env_var: str, value: str = "vim.fn.expand('%:p')"
):
    output = set_nvim_active_file_env_var(pane, env_var, value)
    print(f"\nOutput1: {output}\n\n")
    output2 = send_command_back_to_tmux(
        pane, f"terminal tmux setenv {env_var} ${env_var}"
    )
    # output2 = subprocess.run(
    #    ["terminal", "tmux", "setenv", env_var, f"${env_var}"],
    #    capture_output=True,
    #    text=True,
    # )
    return output2


def get_active_files(session_name: str = None) -> List[Dict[str, str]]:
    """
    Get a list of active files in the specified tmux session or current session if none specified.

    Args:
        session_name (str, optional): Name of tmux session to check. Defaults to current session.

    Returns:
        List[Dict[str, str]]: List of dictionaries containing window, pane, and file information
    """
    server = Server()
    # print(f"\nActive Session: {server.active_session}")
    # print_class_dict(server)
    # Get current session if no session name provided
    if not session_name:
        try:
            # active_session = server.active_session
            # print(f"\nActive Session: {active_session}")
            session = get_current_session(server)
            print(f"\nCalculated Active Session: {session}")
        except IndexError:
            raise RuntimeError("No tmux sessions found")
    else:
        session = server.find_where({"session_name": session_name})
        if not session:
            raise ValueError(f"Session '{session_name}' not found")

    active_files = []

    # Iterate through all windows and panes
    active_pane = session.active_pane
    active_window = session.active_window
    print(f"\nActive Window: {active_window}\n")
    print(f"\nActive Pane: {active_pane}\n")
    active_panes = [p for p in active_window.panes]  # if p.pane_active == "1"]

    dev_pane = active_panes[1]
    # output = send_command_back_to_tmux(
    #    dev_pane, "echo 'Hey'"
    # )  # "echo vim.fn.expand('%:p')")
    # output = set_nvim_active_file_env_var(dev_pane, "ACTIVE_FILE")
    output = set_tmux_env_var_from_nvim(dev_pane, "ACTIVE_FILE3")
    # .communicate()[0])
    # output = dev_pane.send_keys(':terminal echo "vim.fn.expand(%:p)"', enter=True)
    print(f"\nOutput: {output}\n\n")
    # for pane in active_panes:
    #    count += 1
    #    print(f"\n\nPane {count}: ")
    #    print_class_dict(pane)
    # print(f"\nActive Buffer: {active_pane.buffer_name}\n")

    # different_attrs = compare_objects(active_panes)
    # print(f"\nDifferent Attributes in Panes:")
    # for attr in different_attrs:
    #    print(f"    {attr}")

    # print_class_dict(dev_pane)
    for window in session.windows:
        # Print window object:
        # print_class_dict(window)
        # print(f"\nActive Window: {window.name}")
        for pane in window.panes:
            # Print pane object:
            # print_class_dict(pane)
            # Get pane current path
            # pane_path = pane.current_path
            # print(f"Pane: {pane}")
            # for key, val in pane.__dict__.items():
            #    print(f"   {key}: {val}")
            # Get current command running in pane
            pane_cmd = pane.current_command

            # Look for vim/nvim processes and get their file
            if pane_cmd in ["vim", "nvim"]:
                try:
                    # Send keys to get current file (works in normal mode)
                    pane.send_keys(':echo expand("%:p")', enter=True)
                    current_file = pane.cmd("capture-pane", "-p").stdout[-1]

                    # Clear the command line
                    pane.send_keys(':echo ""', enter=True)

                    if current_file:
                        active_files.append(
                            {
                                "window_name": window.name,
                                "pane_id": pane.id,
                                "file_path": current_file,  # os.path.join(pane_path, current_file),
                                "editor": pane_cmd,
                            }
                        )
                except Exception as e:
                    print(f"Error getting file from vim/nvim: {e}")
                    continue

            # Check for other text editors or files open in less/more
            elif pane_cmd in ["less", "more", "bat", "nano", "emacs"]:
                try:
                    process_info = pane.cmd(
                        "list-processes", "-F", "#{pane_current_command}"
                    ).stdout
                    if process_info:
                        active_files.append(
                            {
                                "window_name": window.name,
                                "pane_id": pane.id,
                                "file_path": process_info[0],
                                "editor": pane_cmd,
                            }
                        )
                except Exception as e:
                    print(f"Error getting file from {pane_cmd}: {e}")
                    continue

    return active_files


def main():
    parser = argparse.ArgumentParser(description="List active files in tmux session")
    parser.add_argument(
        "-s", "--session", help="TMux session name (defaults to current session)"
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["plain", "json"],
        default="plain",
        help="Output format (default: plain)",
    )
    args = parser.parse_args()

    try:
        files = get_active_files(args.session)

        for file in files:
            print(file)

        if args.format == "json":
            import json

            print(json.dumps(files, indent=2))
        else:
            for file_info in files:
                print(f"Window: {file_info['window_name']}")
                print(f"Pane: {file_info['pane_id']}")
                print(f"File: {file_info['file_path']}")
                print(f"Editor: {file_info['editor']}")
                print("-" * 40)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


def script():
    exit(main())


if __name__ == "__main__":
    exit(main())
