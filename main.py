#!/usr/bin/env python
"""
Login to mygreekstudy.com and download the CSV data
"""
import csv
import os
import pickle
import sys
from datetime import datetime, timedelta
from io import StringIO

import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

DATA_DIR = "/app"
COOKIE_PATH = os.path.join(DATA_DIR, "cookies.pickle")
KEY_PATH = os.path.join(DATA_DIR, "key.json")

# Setup google api
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a any spreadsheet.
SPREADSHEET_ID = os.environ.get("GOOGLE_SHEET_ID")
RANGE_NAME = os.environ.get("GOOGLE_SHEET_RANGE")

# Define the URLs
BASE_URL = "https://mygreekstudy.com"
LOGIN_URL = f"{BASE_URL}/login.php"
CSV_URL = f"{BASE_URL}/current_report.php"

# Define the login credentials
USERNAME = os.environ.get("GREEKSTUDY_USERNAME")
PASSWORD = os.environ.get("GREEKSTUDY_PASSWORD")

ORGANIZATION = os.environ.get("GREEKSTUDY_ORG")
SCHOOL = os.environ.get("GREEKSTUDY_SCHOOL")


# Create a session to persist cookies across requests


def load_session() -> requests.Session:
    """Load the session from the cookie file"""
    session = requests.Session()

    if os.path.exists(COOKIE_PATH):
        with open(COOKIE_PATH, "rb") as f:
            session.cookies.update(pickle.load(f))

    return session


def login(session: requests.Session):
    """Perform login and store cookies in the session"""

    response = session.post(
        LOGIN_URL,
        data={
            "username": USERNAME,
            "password": PASSWORD,
        },
    )

    # Check if login was successful
    if response.status_code == 200:
        print("Login successful")
    else:
        raise ValueError("Login failed: Invalid username or password")

    # Save the cookies to a file
    with open(COOKIE_PATH, "wb") as f:
        pickle.dump(session.cookies, f)
        print("Login successfully saved")


def get_csv_data(session: requests.Session) -> list[list[str]]:
    """Get the CSV data from mygreekstudy.com"""

    today = datetime.today()
    days_since_last_fri = (today.weekday() - 4) % 7
    days_until_next_thurs = (3 - today.weekday()) % 7

    last_fri = (today - timedelta(days=days_since_last_fri)).strftime("%m/%d/%Y")
    this_thurs = (today + timedelta(days=days_until_next_thurs)).strftime("%m/%d/%Y")

    csv_response = session.get(
        CSV_URL,
        params={
            "reportType": "csv",
            "org": ORGANIZATION,
            "school": SCHOOL,
            "userEmail": USERNAME,
            "to": last_fri,
            "from": this_thurs,
        },
    )

    # Check if export was successful
    if (
        csv_response.status_code == 200
        and csv_response.headers["Content-Type"] == "text/csv"
    ):
        print("CSV data retrieved")
    else:
        raise ValueError("CSV export failed")

    # Decode and clean the CSV data
    csv_data = csv_response.content.decode("utf-8")
    csv_reader = csv.reader(StringIO(csv_data))
    csv_clean = ([cell.strip() for cell in row] for row in csv_reader)

    return list(csv_clean)


def main():
    """Pulls CSV data from mygreekstudy.com and updates a google sheet"""

    # The file key.json stores the service account private key
    if os.path.exists(KEY_PATH):
        creds = Credentials.from_service_account_file(KEY_PATH, scopes=SCOPES)
    else:
        raise ValueError("No service account key found")

    session = load_session()
    # Check if cookies are empty, if so login
    if not session.cookies:
        login(session)

    # For the case when the cookies are invalid, meanning the session has expired
    try:
        csv_data = get_csv_data(session)
    except ValueError:
        print("CSV retrieval failed. Retrying login")
        login(session)
        csv_data = get_csv_data(session)

    try:
        sheet = build("sheets", "v4", credentials=creds).spreadsheets()

        # Update the spreadsheet
        result = (
            sheet.values()
            .update(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME,
                valueInputOption="USER_ENTERED",
                body={"values": csv_data},
            )
            .execute()
        )

        print(f"Successfully updated {result.get('updatedCells')} cells")

    except HttpError as err:
        print(err)
        sys.exit(1)
    except ValueError as err:
        print(err)
        sys.exit(1)


if __name__ == "__main__":
    main()
