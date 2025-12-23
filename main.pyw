import subprocess
import os

BASE_DIR = os.path.dirname(__file__)  # pasta onde o script atual está
p = os.path.join(BASE_DIR, "dashboard.py")

cmd = f'python -m streamlit run "{p}"'

subprocess.Popen(cmd)