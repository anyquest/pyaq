import asyncio
import sys

from aq.containers import get_broker


if __name__ == "__main__":
    if len(sys.argv) <= 1:
        print("Usage: python " + sys.argv[0] + " <app file> <activity name> <file path>")
    else:
        broker = get_broker()
        rv = asyncio.run(broker.run(*sys.argv[1:]))
        print(rv)
