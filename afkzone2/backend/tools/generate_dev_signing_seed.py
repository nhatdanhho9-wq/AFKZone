import base64
import os


def main() -> None:
    seed = os.urandom(32)
    print(base64.b64encode(seed).decode("ascii"))


if __name__ == "__main__":
    main()

