"""Validate the Martenweave skills layer structure.

Checks that all required skill directories exist, each contains a SKILL.md,
and every SKILL.md has the required sections.
"""

from __future__ import annotations

import os
import re
import sys

SKILLS_DIR = "skills"
REQUIRED_SKILLS = [
    "project-orientation",
    "github-issue-loop",
    "validation",
    "memory-and-process-hygiene",
    "model-registry-core",
    "dataset-gap-analysis",
    "impact-analysis",
    "patch-proposal",
]
REQUIRED_SECTIONS = [
    "When to use",
    "Inputs",
    "Read first",
    "Do not do",
    "Procedure",
    "Validation",
    "Output format",
]


def validate_skills() -> int:
    errors = 0

    for skill_name in REQUIRED_SKILLS:
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        if not os.path.isdir(skill_dir):
            print(f"MISSING DIR: {skill_dir}")
            errors += 1
            continue

        skill_file = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_file):
            print(f"MISSING FILE: {skill_file}")
            errors += 1
            continue

        text = open(skill_file, encoding="utf-8").read()
        for section in REQUIRED_SECTIONS:
            pattern = rf"^## {re.escape(section)}$"
            if not re.search(pattern, text, re.MULTILINE):
                print(f"MISSING SECTION '{section}' in {skill_file}")
                errors += 1

    readme_path = os.path.join(SKILLS_DIR, "README.md")
    if not os.path.isfile(readme_path):
        print(f"MISSING FILE: {readme_path}")
        errors += 1

    if errors:
        print(f"\nValidation failed with {errors} error(s).")
        return 1

    print("All skills present and structurally valid.")
    return 0


if __name__ == "__main__":
    sys.exit(validate_skills())
