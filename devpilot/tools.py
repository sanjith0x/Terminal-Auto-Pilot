import os
import subprocess

def run_command(command: str) -> str:
    """Executes a terminal command and returns stdout or stderr."""
    try:
        result = subprocess.run(command, shell=True, text=True, capture_output=True)
        out = result.stdout.strip()
        err = result.stderr.strip()
        if result.returncode != 0:
            return f"Error Code: {result.returncode}\nStderr: {err}\nStdout: {out}"
        return f"Success.\nOutput: {out}" if out else "Success (no output)."
    except Exception as e:
        return f"Execution failed: {str(e)}"

def read_file(filepath: str) -> str:
    """Reads a file so the AI can debug code or logs."""
    if not os.path.exists(filepath):
        return f"File not found: {filepath}"
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Failed to read file: {str(e)}"

def write_file(filepath: str, content: str) -> str:
    """Creates boilerplate code or writes fixes to a file."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Failed to write file: {str(e)}"