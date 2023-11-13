# GSheetStringsSyncer

<p align="center">
  <img src="logo.png" alt="GSheetStringsSyncer Logo" width="400"/>
</p>

GSheetStringsSyncer is a tool designed to facilitate two-way synchronization between Apple's `*.strings` files and a Google Sheets document. This utility is particularly useful for managing localization in software development projects, allowing for efficient translation and localization management through Google Sheets.

## Prerequisites

Before you begin, ensure you have `pyenv` installed on your system for managing multiple Python versions. If `pyenv` is not installed, please follow the [pyenv installation guide](https://github.com/pyenv/pyenv#installation).

## Installation

### Setting Up Python Environment

1. **Install Python 3.10.4 using pyenv**:
   ```sh
   pyenv install 3.10.4
   ```

2. **Set Python 3.10.4 as the local version**:
   ```sh
   pyenv local 3.10.4
   ```

3. **Check the Python version** (optional):
   ```sh
   python --version
   # Output should be Python 3.10.4
   ```

### Creating a Virtual Environment

It is recommended to use a virtual environment for Python projects to manage dependencies effectively.

1. **Create a Virtual Environment (.venv)**:
   Navigate to your project's root directory and run:
   ```sh
   python -m venv .venv
   ```

2. **Activate the Virtual Environment**:
   - On Windows:
     ```sh
     .venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```sh
     source .venv/bin/activate
     ```

3. **Install Required Packages**:
   If you have a `requirements.txt` file, install the required packages using:
   ```sh
   pip install -r requirements.txt
   ```

## Usage

To use GSheetStringsSyncer, you'll need to provide several command-line arguments to specify the operation mode, Google Sheet URL, the name of the sheet, the path to the Resources folder, and the name of the localization file.

### Command-Line Arguments

- `--operation`: Specify the operation mode, either `upload` or `download`.
- `--sheet-url`: Provide the URL of the Google Sheet.
- `--sheet-name`: Specify the name of the sheet within the Google Sheet document.
- `--resources-path`: Set the path to the Resources folder containing the `.strings` files.
- `--file-name`: Provide the name of the localization file.

### Example Commands

- **Uploading to Google Sheets**:
  ```sh
  python gsheet_strings_syncer.py --operation upload --sheet-url "<SHEET_URL>" --sheet-name "<SHEET_NAME>" --resources-path "<RESOURCES_PATH>" --file-name "<FILE_NAME>"
  ```
- **Downloading from Google Sheets**:
  ```sh
  python gsheet_strings_syncer.py --operation download --sheet-url "<SHEET_URL>" --sheet-name "<SHEET_NAME>" --resources-path "<RESOURCES_PATH>" --file-name "<FILE_NAME>"
  ```

Replace `<SHEET_URL>`, `<SHEET_NAME>`, `<RESOURCES_PATH>`, and `<FILE_NAME>` with your specific Google Sheet URL, sheet name, path to the Resources folder, and the name of your localization file, respectively.

## Notes

- Ensure that the Google Sheets API is properly configured with the necessary credentials.
- Follow the specific format in the Google Sheet for the tool to work correctly (with comments in the first column, keys in the second column, and translations in subsequent columns).


