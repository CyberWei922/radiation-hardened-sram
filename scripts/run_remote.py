"""Run a local UTF-8 shell script in the course VM over the ic618 SSH alias."""
from pathlib import Path
import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("--log", type=Path)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    script = args.script.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "ic618", "bash", "-s"],
        input=script.encode("utf-8"), capture_output=True, timeout=args.timeout,
    )
    output = result.stdout.decode("utf-8", "replace")
    error = result.stderr.decode("utf-8", "replace")
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        args.log.write_text(output + ("\nSTDERR:\n" + error if error else ""), encoding="utf-8")
    sys.stdout.write(output)
    sys.stderr.write(error)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
