from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
import re
import argparse
import json

# << Common Starts

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

languages = [
    ("en", "English"),
    ("ar", "Arabic"),
    ("de", "German"),
    ("es", "Spanish"),
    ("fa", "Persian / Farsi"),
    ("fr", "French"),
    ("kk", "Kazakh"),
    ("ms", "Malay"),
    ("nl", "Dutch"),
    ("pt", "Portuguese"),
    ("ru", "Russian"),
    ("tr", "Turkish"),
    ("ug", "Uighur"),
    ("uz", "Uzbek"),
    ("vi", "Vietnamese"),
    ("zh", "Chinese")
]


def extract_sheet_id_from_url(url):
    # Regular expression pattern for extracting the Sheet ID
    pattern = r"/spreadsheets/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, url)

    # Return the matched group (Sheet ID) if found
    if match:
        return match.group(1)
    else:
        return "No Sheet ID found in URL"


def column_letter(number):
    string = ""
    while number > 0:
        number, remainder = divmod(number - 1, 26)
        string = chr(65 + remainder) + string
    return string


def item_or_empty(array, index):
    return array[index] if index < len(array) else ''


def start_sheets_service():
    credentials = None
    # The file token.pickle stores the user's access and refresh tokens.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    service = build('sheets', 'v4', credentials=credentials)

    # Call the Sheets API
    sheet = service.spreadsheets()
    return sheet


def download_from_sheets(sheet_service, spreadsheet_id, sheet_name, num_columns):
    result = sheet_service.values().get(spreadsheetId=spreadsheet_id,
                                        range=f"{sheet_name}!A1:{column_letter(num_columns)}").execute()
    values = result.get('values', [])
    return values

# Common Ends >>


def upload_to_sheets(sheet_service, spreadsheet_id, sheet_name, values, column_index_start, column_index_end):
    range = f"{sheet_name}!{column_letter(column_index_start)}1:{column_letter(column_index_end)}{len(values)}"
    body = {'values': values}
    result = sheet_service.values().update(
        spreadsheetId=spreadsheet_id, range=range,
        valueInputOption="RAW", body=body).execute()
    print(f"Uploaded column '{values[0][0]}' => {result}")


def assign_with_filling(lst, index, value, fill_value=''):
    # Extend the list with the fill_value if necessary
    if index >= len(lst):
        lst.extend([fill_value] * (index - len(lst) + 1))

    # Assign the value to the desired index
    lst[index] = value


def upload_chatgpt_translations(args):
    sheet_service = start_sheets_service()
    sheet_id = extract_sheet_id_from_url(args.sheet_url)
    file_name = args.file_name
    sheet_name = args.sheet_name
    columns = len(languages) * 2 + 2

    values = download_from_sheets(sheet_service, sheet_id, sheet_name, columns)

    with open(file_name, 'r') as file:
        gpt_translations = json.load(file)

    key_column = 1

    for lang_index, lang in enumerate(languages):
        language_code, _ = lang

        metadata_index = lang_index * 2 + 2
        value_index = metadata_index + 1

        # Write the header
        for row_index, row in enumerate(values):
            if row_index < 2:  # Ignore comment and header rows
                continue

            key = item_or_empty(row, key_column)
            value = item_or_empty(row, value_index)
            if key != "" and value == "":
                gpt_translation = gpt_translations.get(key, {}).get(language_code, '')
                if gpt_translation == '':
                    if key in gpt_translations:
                        print(f"🛑 Error: missing translation {language_code}/{key}")
                    continue
                metadata = 'Translated by ChatGPT; human review required.'
                assign_with_filling(values[row_index], value_index, gpt_translation)
                values[row_index][metadata_index] = metadata
                print(f"Using ChatGPT translation {language_code}/{key}")

    upload_to_sheets(sheet_service, sheet_id, sheet_name, values, 1, columns)


def parse_args():
    parser = argparse.ArgumentParser(description='Upload ChatGPT translations with Google Sheets')
    parser.add_argument('--sheet-url', required=True, help='Google Sheet URL')
    parser.add_argument('--sheet-name', required=True, help='The name of the sheet')
    parser.add_argument('--file-name', required=True, help='Localization file name')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    # Use args.sheet, args.resources_path, and args.language_file in your script
    print(f"Sheet URL: {args.sheet_url}")
    print(f"Sheet Name: {args.sheet_name}")
    print(f"File Name: {args.file_name}")

    upload_chatgpt_translations(args)
