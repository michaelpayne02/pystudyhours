"""
Login to mygreekstudy.com and download the CSV data
"""
import sys
import os
import csv
import requests
from io import StringIO
import itertools

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
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

# Create a session to persist cookies across requests
session = requests.Session()


def get_csv_data() -> csv.reader:
    """Get the CSV data from mygreekstudy.com"""
    try:
        # Perform login and store cookies in the session
        response = session.post(
            login_url,
            data={
                "username": username,
                "password": password,
            },
        )

        # Check if login was successful
        if response.status_code == 200:
            print("Login successful")
        else:
            raise ValueError("Login failed: Invalid username or password")

        # Get the CSV data
        csv_response = session.get(
            csv_url,
            params={
                "reportType": "csv",
                "org": org,
                "school": school,
                "userEmail": username,
                "to": "",
                "from": "",
            },
        )

        if (
            csv_response.status_code == 200
            and csv_response.headers["Content-Type"] == "text/csv"
        ):
            print("CSV data retrieved")
        else:
            raise ValueError("CSV data retrieval failed.")

        csv_data = csv_response.content.decode("utf-8")

        csv_reader = csv.reader(StringIO(csv_data))

        # trim all whitespace from the CSV data
        csv_clean = ([cell.strip() for cell in row] for row in csv_reader)
        return csv_clean

    except ValueError:
        sys.exit(1)


def main():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    try:
        # pylint: disable=no-member
        sheet = build("sheets", "v4", credentials=creds).spreadsheets()

        # Get the CSV data
        csv_data = get_csv_data()

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


if __name__ == "__main__":
    main()
