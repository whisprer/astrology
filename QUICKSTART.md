\# Quick Start for Contributors



\## One-Time Setup



Fork on GitHub first, then:

git clone https://github.com/YOUR\_USERNAME/astrology.git

cd astrology

git remote add upstream https://github.com/ORIGINAL\_OWNER/astrology.git

python -m venv venv

source venv/Scripts/activate # or venv/bin/activate on Mac/Linux

pip install pyswisseph pytz geopy



text



\## Every Time You Work



Update your fork with latest changes

git checkout main

git pull upstream main

git push origin main



Create feature branch

git checkout -b my-feature



Make changes, then:

git add .

git commit -m "Description"

git push origin my-feature



Then create Pull Request on GitHub

text



\## Testing



python src/woflstrology-v0.0.5.py

