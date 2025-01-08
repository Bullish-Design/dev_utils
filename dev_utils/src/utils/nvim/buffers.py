from pynvim import attach
import os
import json
from typing import List, Dict, Optional

from dev_utils.src.utils.nvim.nvim_init import NVIM_SOCKET_DEV, NVIM_SOCKET_NOTES


class NeovimBufferLister:
    def __init__(self, socket_path: Optional[str] = None):
        """
        Initialize connection to Neovim.

        Args:
            socket_path: Path to Neovim socket. If None, will try to find from $NVIM_LISTEN_ADDRESS
        """
        self.nvim = self._connect_to_nvim(socket_path)

    def _connect_to_nvim(self, socket_path: Optional[str] = None):
        """
        Connect to Neovim instance via socket.

        Args:
            socket_path: Path to Neovim socket. If None, will try to find from $NVIM_LISTEN_ADDRESS

        Returns:
            Neovim instance
        """
        # env_list = os.environ

        # print(f"Environment variables:")
        # for k, v in env_list.items():
        #    if ":" in v:
        #        v = v.split(":")
        #        print(f"\n   {k}:")
        #        for val in v:
        #            print(f"      - {val}")
        #    else:
        #        print(f"\n   {k} = {v}")
        # print(f"\n\n")

        if socket_path is None:
            socket_path = os.environ.get("NVIM_LISTEN_ADDRESS")

        if not socket_path:
            raise ValueError(
                "No socket path provided and NVIM_LISTEN_ADDRESS environment variable not set. "
                "Please either provide a socket path or ensure NVIM_LISTEN_ADDRESS is set."
            )

        # print(f"Path 1: {socket_path.strip()}")
        # print(f"Path 2: {os.path.join("",socket_path)}")

        if not os.path.exists(socket_path):
            raise FileNotFoundError(f"Neovim socket not found at {socket_path}")

        sesh = attach("socket", path=socket_path)
        # print(f"\n\nSession: {sesh}\n\n")
        return sesh

    def get_buffer_list(self) -> List[Dict[str, str]]:
        """
        Execute :buffers command and parse its output.

        Returns:
            List of dictionaries containing buffer information
        """
        # Save current output of :buffers to a temporary buffer
        self.nvim.command("redir => g:buffer_list")
        self.nvim.command("silent buffers")
        self.nvim.command("redir END")

        # Get the content from the temporary variable
        buffer_output = self.nvim.eval("g:buffer_list")

        # Clean up the temporary variable
        self.nvim.command("unlet g:buffer_list")

        return self._parse_buffer_output(buffer_output)

    def _parse_buffer_output(self, buffer_output: str) -> List[Dict[str, str]]:
        """
        Parse the output of :buffers command into structured data.

        Args:
            buffer_output: Raw output from :buffers command

        Returns:
            List of dictionaries containing parsed buffer information
        """
        buffers = []
        for line in buffer_output.split("\n"):
            line = line.strip()
            if not line:
                continue

            # Parse the buffer line. Format is typically:
            # "1 %a   "file.txt"                    line 1"
            try:
                # Split by whitespace, but keep quoted strings intact
                parts = line.split()

                # Get buffer number
                buffer_num = parts[0]

                # Get buffer flags
                flags = parts[1] if len(parts) > 1 else ""

                # Get filename - it's usually in quotes
                filename = None
                for part in parts[2:]:
                    if part.startswith('"') and part.endswith('"'):
                        filename = part.strip('"')
                        break

                # Get line number if present
                line_num = None
                for i, part in enumerate(parts):
                    if part == "line":
                        line_num = parts[i + 1]
                        break

                buffers.append(
                    {
                        "number": buffer_num,
                        "flags": flags,
                        "filename": filename or "[No Name]",
                        "line": line_num or "1",
                        "active": "%" in flags,
                        "modified": "+" in flags,
                        "hidden": "h" in flags,
                    }
                )

            except Exception as e:
                print(f"Error parsing buffer line '{line}': {e}")
                continue

        return buffers


def main():
    try:
        # Create buffer lister instance
        buffer_lister = NeovimBufferLister(socket_path=NVIM_SOCKET_DEV)

        print(f"\nBuffer_lister: {buffer_lister}\n")
        # Get and display buffer list
        buffers = buffer_lister.get_buffer_list()

        # Print in both human-readable and JSON formats
        print("Buffer List:")
        print("-" * 50)
        for buf in buffers:
            status = []
            if buf["active"]:
                status.append("active")
            if buf["modified"]:
                status.append("modified")
            if buf["hidden"]:
                status.append("hidden")

            print(f"Buffer {buf['number']}: {buf['filename']}")
            print(f"  Line: {buf['line']}")
            print(f"  Status: {', '.join(status) if status else 'normal'}")
            print()

        print("\nJSON output:")
        print(json.dumps(buffers, indent=2))

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
