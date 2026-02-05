import os

# Resolve project root (independent of current working directory)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# Base directory where per-task working directories are created
RUNS_BASE_DIR = os.environ.get(
	"VC_RUN_DIR",
	os.path.join(PROJECT_ROOT, "runs")
)

# Ensure the base dir exists
os.makedirs(RUNS_BASE_DIR, exist_ok=True)

# Public outputs directory (served via StaticFiles at /outputs)
OUTPUTS_DIR = os.path.join(RUNS_BASE_DIR, "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)
