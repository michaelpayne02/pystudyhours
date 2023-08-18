#!/usr/bin/env python
"""
Login to mygreekstudy.com and download the CSV data
"""
import sys
import os
import csv
from io import StringIO
import requests

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the login credentials
username = os.environ.get("GREEKSTUDY_USERNAME")
password = os.environ.get("GREEKSTUDY_PASSWORD")

org = os.environ.get("GREEKSTUDY_ORG")
school = os.environ.get("GREEKSTUDY_SCHOOL")

# Setup google api
# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
spreadsheet_id = os.environ.get("GOOGLE_SHEET_ID")
range_name = os.environ.get("GOOGLE_SHEET_RANGE")

# Define the URLs
BASE_URL = "https://mygreekstudy.com"  # Replace with the actual base URL
login_url = f"{BASE_URL}/login.php"
csv_url = f"{BASE_URL}/current_report.php"

login_data = {
    "username": username,
    "password": password,
}

csv_params = {
    "reportType": "csv",
    "org": org,
    "school": school,
    "userEmail": username,
    "to": "",
    "from": "",
}

# Create a session to persist cookies across requests
session = requests.Session()


def get_csv_data() -> csv.reader:
    """Get the CSV data from mygreekstudy.com"""
    try:
        # Perform login and store cookies in the session
        response = session.post(
            login_url,
            data=login_data,
        )

        # Check if login was successful
        if response.status_code == 200:
            print("Login successful")
        else:
            raise ValueError("Login failed: Invalid username or password")

        # Get the CSV data
        csv_response = session.get(
            csv_url,
            params=csv_params,
        )

        # Check if export was successful
        if (
            csv_response.status_code == 200
            and csv_response.headers["Content-Type"] == "text/csv"
        ):
            print("CSV data retrieved")
        else:
            raise ValueError("CSV data retrieval failed.")

        # Decode and clean the CSV data
        csv_data = csv_response.content.decode("utf-8")
        csv_reader = csv.reader(StringIO(csv_data))
        csv_clean = ([cell.strip() for cell in row] for row in csv_reader)

        return csv_clean

    except ValueError as err:
        print(err)
        sys.exit(1)


def main():
    """Shows basic usage of the Sheets API.
    Replace spreadsheetId and range with values from csv
    """
    # The file key.json stores the service account private key
    os.chdir("/app")
    if os.path.exists("key.json"):
        creds = Credentials.from_service_account_file("key.json", scopes=SCOPES)
    else:
        raise ValueError("No service account key found.")

    try:
        # pylint: disable=no-member
        sheet = build("sheets", "v4", credentials=creds).spreadsheets()

        # Get the CSV data
        csv_data = get_csv_data()

        # Update the spreadsheet
        result = (
            sheet.values()
            .update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption="USER_ENTERED",
                body={"values": list(csv_data)},
            )
            .execute()
        )

        print(f"Successfully updated {result.get('updatedCells')} cells.")

    except HttpError as err:
        print(err)
        sys.exit(1)


if __name__ == "__main__":
    main()
