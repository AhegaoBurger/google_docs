import configparser
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googletrans import Translator
from flask import Flask, jsonify

app = Flask(__name__)


def process_document():
    # Initialize the translator
    translator = Translator()

    # Initialize the configparser
    config = configparser.ConfigParser()

    # Read the configuration file
    config.read('config.ini')

    # Use service account credentials to access Google Docs
    creds = Credentials.from_service_account_file(config.get('Google', 'json_file'))

    # Build the Google Docs service
    docs_service = build('docs', 'v1', credentials=creds)

    # Build the Google Sheets service
    sheets_service = build('sheets', 'v4', credentials=creds)

    # The ID and range of the Google Sheets document.
    spreadsheet_id = config.get('Google', 'spreadsheet_id')
    range_ = config.get('Google', 'range')  # adjust as necessary

    # Retrieve the records from the Google Sheets document
    result = sheets_service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_).execute()
    records = result.get('values', [])

    # Prepare a dictionary to hold placeholders and their corresponding values
    # Here, we assume that records is a list of lists, where each inner list has two elements: key and value.
    data = {record[0]: record[1] for record in records}

    # The ID of the document to update.
    document_id = config.get('Google', 'document_id')

    # Find and replace placeholders with corresponding data
    for placeholder, value in data.items():
        requests = [
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{' + placeholder + '}}',
                        'matchCase':  'true'
                    },
                    'replaceText': value,
                }
            },
        ]
        result = docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()

    # Translate values to Portuguese and replace placeholders for the second page
    for placeholder, value in data.items():
        # Translate the value to Portuguese
        translated_value = translator.translate(value, dest='pt').text

        requests = [
            {
                'replaceAllText': {
                    'containsText': {
                        'text': '{{' + placeholder + '_pt}}',
                        'matchCase': 'true'
                    },
                    'replaceText': translated_value,
                }
            },
        ]
        result = docs_service.documents().batchUpdate(documentId=document_id, body={'requests': requests}).execute()

    return result

@app.route('/api/process', methods=['GET'])
def api_process():
    try:
        result = process_document()
        return jsonify(result=result)
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
