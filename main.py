import subprocess, os

BASE_DIR = os.path.dirname(__file__)
p = os.path.join(BASE_DIR, "dashboard.py")
subprocess.Popen(["python - m", "-m streamlit run", p])
