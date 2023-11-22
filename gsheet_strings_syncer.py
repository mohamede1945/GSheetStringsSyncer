from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
import re
import argparse


class Struct:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)


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
reference_index = 0
empty_line = '<<< EMPTY LINE >>>'
metadata_prefix = '// Metadata:'

no_translation = Struct(key='', value='', metadata='')


def extract_sheet_id_from_url(url):
    # Regular expression pattern for extracting the Sheet ID
    pattern = r"/spreadsheets/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, url)

    # Return the matched group (Sheet ID) if found
    if match:
        return match.group(1)
    else:
        return "No Sheet ID found in URL"


def decode_escaped_string(value):
    return value.encode('raw_unicode_escape').decode('unicode_escape')


def encode_escaped_string(value):
    return value.replace("\n", "\\n")


def item_or_empty(array, index):
    return array[index] if index < len(array) else ''


def column_letter(number):
    string = ""
    while number > 0:
        number, remainder = divmod(number - 1, 26)
        string = chr(65 + remainder) + string
    return string


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


def append_comment(list, comment, combine_comments):
    # Amend to the comment if not changed
    if combine_comments and len(list) > 0 and isinstance(list[-1], str):
        list[-1] = f"{list[-1]}\n{comment}"
    else:
        list.append(comment)


def extract_metadata(list):
    metadata = ""
    if len(list) > 0 and isinstance(list[-1], str):
        # Last comment could have been joined before into multiple lines.
        comment_lines = list[-1].split('\n')
        if comment_lines[-1].startswith(metadata_prefix):
            metadata = comment_lines[-1].replace(metadata_prefix, '').strip()
            list.pop()
            # If the comment has more than 1 lines, keep the other lines and remove the metadata one.
            if len(comment_lines) > 1:
                list.append('\n'.join(comment_lines[:-1]))
    return metadata


def parse_localizable_file(file_path, combine_comments):
    with open(file_path, 'r', encoding='utf-8') as file:
        file_lines = file.readlines()

    lines = []
    dict = {}
    current_comment = ""

    header = ""

    for line in file_lines:
        line = line.strip('\n')
        stripped_line = line.strip()

        # Handle multi-line comments
        if stripped_line.startswith('/*'):
            current_comment = line + "\n"  # Start a new comment
        elif stripped_line.endswith('*/'):
            current_comment += line  # End of multi-line comment
            if header:
                append_comment(lines, current_comment, combine_comments)
            else:
                header = current_comment

            current_comment = ""
        elif current_comment:
            current_comment += line + "\n"  # Continue multi-line comment

        # Handle single-line comments
        elif stripped_line.startswith('//'):
            append_comment(lines, line, combine_comments)

        # Handle empty lines
        elif not stripped_line:
            append_comment(lines, empty_line, combine_comments)

        # Handle key-value pairs
        elif '"' in line:
            match = re.search(r'"(.*?)"\s*=\s*"(.*?)";', line)
            if match:
                key, value = match.groups()
                value = decode_escaped_string(value)
                metadata = extract_metadata(lines)
                translation = Struct(key=key, value=value, metadata=metadata)
                dict[key] = translation
                lines.append(translation)

    return Struct(header=header, lines=lines, dict=dict)


def upload_to_sheets(sheet_service, spreadsheet_id, sheet_name, values, column_index):
    range = f"{sheet_name}!{column_letter(column_index)}1:{column_letter(column_index)}{len(values)}"
    body = {'values': values}
    result = sheet_service.values().update(
        spreadsheetId=spreadsheet_id, range=range,
        valueInputOption="RAW", body=body).execute()
    print(f"Uploaded column '{values[0][0]}' => {result}")


def is_comment(line):
    return isinstance(line, str)


def is_translation(line):
    return isinstance(line, Struct) and hasattr(line, 'key') and hasattr(line, 'value')


def translation_data(reference, translation, attribute):
    return [getattr(translation.dict.get(line.key, no_translation), attribute)
            if is_translation(line) else "" for line in reference.lines]


def upload_translations_to_sheets(sheet_service, spreadsheet_id, sheet_name, lang, reference, translation, column_index):
    # Prepare values for the translations column C, D, etc
    language = f"{lang[0]} - {lang[1]}"
    translation_metadata = translation_data(reference, translation, 'metadata')
    translation_values = translation_data(reference, translation, 'value')

    metadata = [[language]] + [['METADATA']] + [[value] for value in translation_metadata]
    upload_to_sheets(sheet_service, spreadsheet_id, sheet_name, metadata, column_index)
    
    values = [[language]] + [[translation.header]] + [[value] for value in translation_values]
    upload_to_sheets(sheet_service, spreadsheet_id, sheet_name, values, column_index + 1)


def upload_keys_to_sheets(sheet_service, spreadsheet_id, sheet_name, reference):
    # Prepare comments for column A
    comments = [line if is_comment(line) else "" for line in reference.lines]
    comments_values = [["Comments"], ["Header"]] + [[comment] for comment in comments]
    upload_to_sheets(sheet_service, spreadsheet_id, sheet_name, comments_values, 1)

    # Prepare keys for column B
    keys = [line.key if is_translation(line) else "" for line in reference.lines]
    keys_values = [["Key"], [""]] + [[key] for key in keys]
    upload_to_sheets(sheet_service, spreadsheet_id, sheet_name, keys_values, 2)


def upload_localizable_files(sheet_service, sheet_id, sheet_name, languages, resources_path, file_name):
    # Assume keys are the same for all languages, so use the first language for keys
    reference_lang_path = os.path.join(resources_path, f'{languages[reference_index][0]}.lproj/{file_name}')
    reference = parse_localizable_file(reference_lang_path, True)

    # Upload keys to the first column
    upload_keys_to_sheets(sheet_service, sheet_id, sheet_name, reference)

    # Upload translations for each language
    for index, lang in enumerate(languages):
        file_path = os.path.join(resources_path, f'{lang[0]}.lproj/{file_name}')
        translation = parse_localizable_file(file_path, False)
        upload_translations_to_sheets(sheet_service, sheet_id, sheet_name, lang, reference, translation, index * 2 + 3)


def download_from_sheets(sheet_service, spreadsheet_id, sheet_name, num_columns):
    result = sheet_service.values().get(spreadsheetId=spreadsheet_id,
                                        range=f"{sheet_name}!A1:{column_letter(num_columns)}").execute()
    values = result.get('values', [])
    return values


def download_localizable_files(sheet_service, spreadsheet_id, sheet_name, languages, resources_path, file_name):
    values = download_from_sheets(sheet_service, spreadsheet_id, sheet_name, len(languages) * 2 + 2)
    comments_column = 0
    key_column = 1

    for index, lang in enumerate(languages):
        language_code, _ = lang
        file_path = f"{language_code}.lproj/{file_name}"
        output_path = os.path.join(resources_path, file_path)
        with open(output_path, 'w', encoding='utf-8') as file:
            metadata_index = index * 2 + 2
            value_index = metadata_index + 1

            # Write the header
            header = item_or_empty(values[1], value_index)
            if header != "":
                file.write(f"{header}\n")

            for row in values[2:]:
                comment = item_or_empty(row, comments_column)
                key = item_or_empty(row, key_column)
                metadata = item_or_empty(row, metadata_index)
                value = item_or_empty(row, value_index)
                if comment != "":
                    formatted_comment = comment.replace(empty_line, "")
                    file.write(f"{formatted_comment}\n")
                elif key != "" and value != "":
                    if metadata != "":
                        file.write(f"{metadata_prefix} {metadata}\n")
                    file.write(f'"{key}" = "{encode_escaped_string(value)}";\n')
        print(f"Downloaded '{file_path}")


def main(args):
    sheet_service = start_sheets_service()
    sheet_id = extract_sheet_id_from_url(args.sheet_url)
    resources_path = args.resources_path
    file_name = args.file_name
    sheet_name = args.sheet_name
    operation = args.operation

    if operation == 'download':
        download_localizable_files(sheet_service, sheet_id, sheet_name, languages, resources_path, file_name)
    elif operation == 'upload':
        upload_localizable_files(sheet_service, sheet_id, sheet_name, languages, resources_path, file_name)


def parse_args():
    parser = argparse.ArgumentParser(description='Sync Localizable.strings with Google Sheets')
    parser.add_argument('--operation', required=True,
                        choices=['upload', 'download'], help='Operation mode: upload or download')
    parser.add_argument('--sheet-url', required=True, help='Google Sheet URL')
    parser.add_argument('--sheet-name', required=True, help='The name of the sheet')
    parser.add_argument('--resources-path', required=True, help='Path to the Resources folder')
    parser.add_argument('--file-name', required=True, help='Localization file name')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()

    # Use args.sheet, args.resources_path, and args.language_file in your script
    print(f"Operation: {args.operation}")
    print(f"Sheet URL: {args.sheet_url}")
    print(f"Sheet Name: {args.sheet_name}")
    print(f"Resources Path: {args.resources_path}")
    print(f"File Name: {args.file_name}")

    main(args)
