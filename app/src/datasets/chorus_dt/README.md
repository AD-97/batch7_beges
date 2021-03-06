# Usage
## Requirements
- Virtualenv
- virtualenvwrapper

## Setup

And fill the missing values.

### Virtualenv
Setup your python environment:
```
mkvirtualenv beges --python 3.6
workon beges
pip install -r requirements.txt
```

### Datasets
Download the raw data using the `dowload_data.sh` script:
`sh scripts/download_data.sh`

If you are on Windows launch `download_data_win.ps1` via PowerShell.

## Usage
You can prepare the different datasets used for places resolution:
```
python scipts/prepare_datasets.py
```
This will create / replaces files in `data/prepared`.

You can resolve the places:
```
python scipts/resolve_places.py
```
This will create / replaces `trips.csv` and `places.csv` in `data/clean`.

You can also run a small dashboard to see names resolution:
```
python dash_dashboard.py
```
It will run a small web app available on the port specified in the `dash` section of the `config.ini` file.
