"""
Entry point for running the radbot agent directly.
"""

from radbot.cli.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())