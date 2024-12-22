import sys
import os
import shlex
import subprocess


def main():
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            raw_input = input().strip()

            if raw_input:
                handle_command(raw_input)

        except EOFError:
            print("\nExiting.")
            sys.exit(0)


def handle_command(raw_input):
    """Handle parsing and execution of the user input."""
    if ">>" in raw_input or ">" in raw_input:
        if ">>" in raw_input:
            redirection_operator = "2>>" if "2>>" in raw_input else ">>"
            append_mode = True
        else:
            redirection_operator = "2>" if "2>" in raw_input else ">"
            append_mode = False

        command_part, redirection_part = map(
            str.strip, raw_input.split(redirection_operator, 1)
        )
        # Handle optional file descriptor
        if command_part.endswith("1"):
            command_part = command_part[:-1]
        elif command_part.endswith("1" + redirection_operator):
            command_part = command_part[: -len(redirection_operator) + 1]
            
        command_parts = parse_command(command_part)
        command_name = command_parts[0]
        command_args = command_parts[1:]

        file_mode = "a" if append_mode else "w"
        try:
            with open(redirection_part, file_mode) as redirect_file:
                if "2" in redirection_operator:
                    execute_command(
                        command_name, command_args, error_file=redirect_file
                    )
                else:
                    execute_command(
                        command_name, command_args, output_file=redirect_file
                    )
        except Exception as e:
            print(f"Error opening file for redirection: {e}")
    else:
        command_parts = parse_command(raw_input)
        command_name = command_parts[0]
        command_args = command_parts[1:]
        execute_command(command_name, command_args)


def parse_command(command):
    """Parse the command and return a list of parts."""
    return shlex.split(command)


def execute_command(
    command_name, command_args, output_file=sys.stdout, error_file=sys.stderr
):
    """Executes a command and handles built-ins, external commands, and redirection."""
    built_in_commands = {
        "exit": exit_command,
        "echo": echo_command,
        "pwd": pwd_command,
        "cd": cd_command,
        "type": type_command,
    }

    if command_name in built_in_commands:
        built_in_commands[command_name](command_args, output_file, error_file)
    else:
        execute_external_command(command_name, command_args, output_file, error_file)


def exit_command(args, output_file, error_file):
    """Handle the 'exit' command."""
    sys.exit(int(args[0]) if args else 0)


def echo_command(args, output_file, error_file):
    """Handle the 'echo' command."""
    print(" ".join(args), file=output_file)


def pwd_command(args, output_file, error_file):
    """Handle the 'pwd' command."""
    print(os.getcwd(), file=output_file)


def cd_command(args, output_file, error_file):
    """Handle the 'cd' command."""
    if not args:
        print("cd: missing argument", file=error_file)
        return

    target_path = os.path.expanduser(args[0])
    try:
        os.chdir(target_path)
    except FileNotFoundError:
        print(f"cd: {target_path}: No such file or directory", file=error_file)
    except NotADirectoryError:
        print(f"cd: {target_path}: Not a directory", file=error_file)
    except PermissionError:
        print(f"cd: {target_path}: Permission denied", file=error_file)


def type_command(args, output_file, error_file):
    """Handle the 'type' command."""
    built_in_commands = ["type", "exit", "echo", "pwd", "cd"]
    if not args:
        print("Usage: type <command>", file=error_file)
        return

    target_command = args[0]
    if target_command in built_in_commands:
        print(f"{target_command} is a shell builtin", file=output_file)
    else:
        for dir in os.environ["PATH"].split(":"):
            full_path = os.path.join(dir, target_command)
            if os.access(full_path, os.X_OK):
                print(f"{target_command} is {full_path}", file=output_file)
                return
        print(f"{target_command}: not found", file=error_file)


def execute_external_command(command_name, command_args, output_file, error_file):
    """Handle execution of external commands."""
    for dir in os.environ["PATH"].split(":"):
        full_path = os.path.join(dir, command_name)
        if os.access(full_path, os.X_OK):
            try:
                subprocess.run(
                    [full_path] + command_args,
                    text=True,
                    stdout=output_file,
                    stderr=error_file,
                )
            except Exception as e:
                print(f"Error executing {command_name}: {e}", file=error_file)
            return
    print(f"{command_name}: command not found", file=error_file)


if __name__ == "__main__":
    main()
