# Entry point for hosting panels expecting main.py
import runpy

if __name__ == "__main__":
    runpy.run_path("CodeX.py", run_name="__main__")
