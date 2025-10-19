import subprocess
import os

# Get the directory of the current script (main.py)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to Home.py
home_py_path = os.path.join(script_dir, "Home.py")

# Check if Home.py exists before trying to run it
if not os.path.exists(home_py_path):
    print(f"Error: Could not find {home_py_path}")
    print("Please make sure Home.py is in the same directory as main.py.")
else:
    print(f"Launching Streamlit app from: {home_py_path}")
    # The command to execute
    command = ["streamlit", "run", home_py_path]

    # Run the command
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("Error: 'streamlit' command not found.")
        print("Please make sure Streamlit is installed and in your system's PATH.")
    except Exception as e:
        print(f"An error occurred: {e}")
