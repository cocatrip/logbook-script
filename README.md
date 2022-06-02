# logbook-script
python script for filling logbook automatically

## Running this app locally

To run this app locally on your machine:

1. Install all required libraries

```pip install requirements.txt```

2. Run the app using gunicorn

```gunicorn app:app --timeout 120 --keep-alive 120```
