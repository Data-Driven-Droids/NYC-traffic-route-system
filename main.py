import subprocess
import os

# Get the PORT from the environment, defaulting to 8080
port = os.environ.get("PORT", "8080")

# Get the directory of the current script (main.py)
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to Home.py
home_py_path = os.path.join(script_dir, "Home.py")

# Check if Home.py exists before trying to run it
if not os.path.exists(home_py_path):
    print(f"Error: Could not find {home_py_path}")
    print("Please make sure Home.py is in the same directory as main.py.")
else:
    print(f"Launching Streamlit app from: {home_py_path} on port {port}")
    
    # The command to execute, now with port and server args
    command = [
        "streamlit", 
        "run", 
        home_py_path, 
        "--server.port", 
        port,
        "--server.enableCORS", 
        "false",
        "--server.enableXsrfProtection",
        "false"
    ]

    # Run the command
    try:
        subprocess.run(command, check=True)
    except FileNotFoundError:
        print("Error: 'streamlit' command not found.")
        print("Please make sure Streamlit is installed and in your system's PATH.")
    except Exception as e:
        print(f"An error occurred: {e}")