"""Entry point (NFR-U1, NFR-U2). Run it with no arguments:

    python -m elevator.main

Every setting is read from elevator.properties, in the elevator/resources folder. The run itself is
done by elevator.runner.

Passing any argument prints a short message and returns exit code 2. A missing settings or request
file, or a bad value, prints the problem and returns exit code 1. Neither prints a stack trace.
"""

import logging
import sys

from elevator.runner import SETTINGS_FILE, read_settings, run_elevator

# Exit code for an unexpected argument (NFR-U2).
EXIT_USAGE = 2

# Exit code for a missing or bad settings file, a bad request file, or a failed run (NFR-I3, NFR-S4).
EXIT_ERROR = 1


def main(argv: list[str] | None = None) -> int:
    """Reads the settings and runs the simulation (FR-OUT-1 to FR-OUT-3).

    Args:
        argv: the command-line arguments after the program name. Must be empty (NFR-U1). Defaults to sys.argv.

    Returns:
        the exit code: 0 on success, 1 on an error, 2 on a usage error.
    """
    args = sys.argv[1:] if argv is None else argv
    if args:
        return _usage(f"this program takes no arguments. Set everything in {SETTINGS_FILE}")

    # Log messages (Boarded, Alighted) go to stderr, as in the Java version.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stderr)
    try:
        run_elevator(read_settings())
    except OSError as error:
        return _error(f"cannot read a file: {error}")
    except (ValueError, RuntimeError) as error:
        return _error(str(error))
    return 0


def _usage(problem: str) -> int:
    """Prints a usage message and returns the usage exit code (NFR-U2).

    Args:
        problem: what was wrong.

    Returns:
        the usage exit code.
    """
    print(problem, file=sys.stderr)
    print("usage: python -m elevator.main", file=sys.stderr)
    return EXIT_USAGE


def _error(message: str) -> int:
    """Prints a run error and returns the error exit code (NFR-I3, NFR-S4).

    Args:
        message: the problem to show.

    Returns:
        the error exit code.
    """
    print(f"error: {message}", file=sys.stderr)
    return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
