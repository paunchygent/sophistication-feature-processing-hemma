"""Launch-only client. Host commands, arguments, environment and paths are not accepted."""
import socket
import sys


def request(path="/run/host-jasp/jasp.sock"):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(20)
        connection.connect(path)
        connection.sendall(b"JASP/1\n")
        with connection.makefile("rb") as stream:
            reply = stream.readline(2048).decode("utf-8", errors="replace").strip()
    if not reply.startswith("OK "):
        raise RuntimeError(reply or "Host JASP launcher closed without acknowledgement")
    return reply[3:]


def main():
    try:
        print(request())
    except (OSError, RuntimeError) as exc:
        print(f"JASP launch was not confirmed: {exc}. Check the desktop before trying again; inspect the host's hemma-jasp socket/unit logs.", file=sys.stderr)
        return 69
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
