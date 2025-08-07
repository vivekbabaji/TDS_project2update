import subprocess
import sys
import traceback
from typing import List

async def run_python_code(code: str, libraries: List[str]) -> str:
    def execute_code():
        exec_globals = {}
        exec(code, exec_globals)

    # Step 1: Install all required libraries first
    for lib in libraries:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
        except Exception as install_error:
            return f"❌ Failed to install library '{lib}':\n{install_error}"

    # Step 2: Execute the code after installation
    try:
        execute_code()
        return "✅ Code executed successfully after installing libraries."

    except Exception as e:
        return f"❌ Error during code execution:\n{traceback.format_exc()}"
