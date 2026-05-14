"""Entry point for ``python -m datascope``."""

from datascope import __version__


def main():
    print(f"datascope {__version__}")
    print()
    print("Usage:")
    print("  python -m datascope          Show this message")
    print("  datascope --help             Full CLI help (coming in a future release)")
    print()
    print("The CLI entry point (datascope.cli:main) will be available after U9.")


if __name__ == "__main__":
    main()
