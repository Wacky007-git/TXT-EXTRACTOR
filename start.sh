echo "Cloning Repo..."
git clone https://github.com/Wacky007-git/TXT-EXTRACTOR
cd /TXT-EXTRACTOR
pip install -r requirements.txt
echo "Starting Bot..."
python -m Extractor
