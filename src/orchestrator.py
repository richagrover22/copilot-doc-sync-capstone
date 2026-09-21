import sys
import os
import subprocess

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.abspath(os.path.dirname(__file__))

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, SRC_DIR)

def run_step(step_name, command):
    print(f"\n=================== [Executing: {step_name}] ===================")
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{SRC_DIR}{os.pathsep}{BASE_DIR}{os.pathsep}{env.get('PYTHONPATH', '')}"
    
    result = subprocess.run(command, shell=True, env=env)
    if result.returncode != 0:
        print(f"❌ Error in {step_name}. Stopping pipeline.")
        sys.exit(1)
    print(f"✅ Successfully completed: {step_name}")

def start_pipeline():
    # 1. Config Validation Gate
    run_step("Step 1: Validate Configuration", "python -m cli config-validate docsync.toml")

    # 2. Check Documentation Status
    run_step("Step 2: Check Documentation Sync Status", "python -m cli check")

    # 3. Preview Documentation Sync (Source: user_story.md, Target: README.md)
    run_step("Step 3: Preview Documentation Changes", "python -m cli sync-preview user_story.md README.md overview")

    # 4. Apply Documentation Sync Changes (Source: user_story.md, Target: README.md)
    run_step("Step 4: Apply Documentation Sync", "python -m cli sync-apply user_story.md README.md overview")

    # 5. Execute Pytest Quality Gate
    run_step("Step 5: Run Pytest Quality Gate", "pytest tests/")

if __name__ == "__main__":
    start_pipeline()