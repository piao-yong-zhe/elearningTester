import sys
from gui import launch_gui


if __name__ == "__main__":
    if len(sys.argv) == 2:
        import asyncio
        from exam_helper import main as run_exam_helper
        asyncio.run(run_exam_helper(sys.argv[1]))
    else:
        launch_gui()
