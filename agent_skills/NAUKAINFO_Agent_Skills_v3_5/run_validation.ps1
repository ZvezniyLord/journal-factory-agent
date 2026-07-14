$ErrorActionPreference = "Stop"
python tests\validate_skills.py
python -m unittest discover -s tests -p "test_*.py" -v
