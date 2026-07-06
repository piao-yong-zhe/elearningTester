import asyncio
import sys
from exam_helper import main as run_exam_helper


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <exam_url>")
        sys.exit(1)
    asyncio.run(run_exam_helper(sys.argv[1]))
