import pathlib

user_story_content = """# User Story

<!-- docsync:START overview -->
Automate documentation sync and validation across repository files.
<!-- docsync:END overview -->
"""

readme_content = """# Documentation Sync Capstone

<!-- docsync:START overview -->
<!-- docsync:END overview -->
"""

pathlib.Path("user_story.md").write_text(user_story_content, encoding="utf-8")
pathlib.Path("README.md").write_text(readme_content, encoding="utf-8")
print("Files created with uppercase markers!")
