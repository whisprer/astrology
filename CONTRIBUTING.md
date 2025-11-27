[CONTRIBUTING.md]

# Contributing to woflStrology

Thanks for for your interest in improving `woflsStrology` - for those wanting to contribute follow instructions below. 🐺 Thanks!


## How to Contribute

### Code Style

- Follow *Python3.14 2025* edition conventions.
- Keep logic minimal — avoid unnecessary dependencies

### 1. Fork the Repository

Click the **Fork** button at the top right of this repo to create your own copy.

### 2. Clone Your Fork

git clone https://github.com/whisprer/astrology.git
cd astrology

### 3. Create a New Branch

Create a branch for your feature/fix
git checkout -b my-awesome-feature

### 4. Make Your Changes

Edit the files in `src/`:
- `woflstrology-vX.X.X.py` - main script
- `horoscope_database.json` - astrological content

### 5. Test Your Changes

Set up virtual environment
```bash
python -m venv venv
./venv/Scripts/activate  # Windows
```

or
```bash
source ./venv/bin/activate  # Linux/macOS

Install dependencies
pip install pyswisseph pytz geopy [pyinstaller for executables; numpy matplotlib pillow for icon_generator]

Testing
Run the build and ensure no regressions:
```bash
python src/woflstrology-vX.X.X.py
```

For manual verification:
Create temporary files.
Compare before/after with a hex viewer or recovery utility.


### 6. Commit Your Changes

Add your changes
git add src/woflstrology-vX.X.X.py
git add src/horoscope_database.json

Commit with a descriptive message
git commit -m "Add new compatibility insights for Air signs"


### 7. Push to Your Fork

git push origin my-awesome-feature


### 8. Create a Pull Request

1. Go to **your fork** on GitHub
2. Click **"Compare & pull request"** button
3. Write a description of your changes
4. Click **"Create pull request"**


## Guidelines

- Keep compatibility interpretations universally applicable (not specific predictions)
- Test your changes before submitting
- Write clear commit messages
- One feature/fix per pull request

Documentation
If you add a feature, please update README.md accordingly.

Communication

Open an Issue for:
Feature requests
Bug reports
Questions or clarifications

## Questions?
Open an issue or reach out!


## Workflow Diagram

                      ┌──────────────────┐
                      │     Original Repo     │
                      │    (your/astrology)   │
                      └────────┬─────────┘
                               │
                       1. Fork │
                               ▼
                      ┌──────────────────┐
                      │      Your Fork        │
                      │   (them/astrology)    │
                      └────────┬─────────┘
                               │
                       2. Clone│
                               ▼
                      ┌──────────────────┐
                      │    Local Machine      │
                      │                       │
                      │   3. Branch           │
                      │   4. Edit             │
                      │   5. Commit           │
                      └────────┬─────────┘
                               │
                       6. Push │
                               ▼
                      ┌──────────────────┐
                      │     Your Fork         │
                      │   (them/astrology)    │
                      └────────┬─────────┘
                               │
                       7. Pull Request
                               ▼
                      ┌──────────────────┐
                      │    Original Repo      │
                      │   (you review &       │
                      │    merge)             │
                      └──────────────────┘


Thanks for helping keep woflStrology clean, efficient, and reliable!