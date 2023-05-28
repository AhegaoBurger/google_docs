import psycopg2
import configparser
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# Initialize the configparser
config = configparser.ConfigParser()

# Read the configuration file
config.read('config.ini')

# Define PostgreSQL connection parameters
params = {
    "host": config.get('PostgreSQL', 'host'),
    "database": config.get('PostgreSQL', 'database'),
    "user": config.get('PostgreSQL', 'user'),
    "password": config.get('PostgreSQL', 'password'),
    "port": config.getint('PostgreSQL', 'port')  # default PostgreSQL port
}

# Connect to your postgres DB
conn = psycopg2.connect(**params)

# Open a cursor to perform database operations
cur = conn.cursor()

# Execute a query
cur.execute("SELECT * FROM student_info")

# Retrieve query results
records = cur.fetchall()

# Prepare a dictionary to hold placeholders and their corresponding values
data = {}

# Assuming each record is a tuple in the form (placeholder, value)
for record in records:
    placeholder, value = record
    data[placeholder] = value

# Use service account credentials to access Google Docs
creds = Credentials.from_service_account_file(config.get('Google', 'json_file'))

service = build('docs', 'v1', credentials=creds)

# The ID of the document to update.
document_id = config.get('Google', 'document_id')

# Get the existing content of the Google Doc
document = service.documents().get(documentId=document_id).execute()
content = document.get('body').get('content')

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

    # Make a request to the Google Docs API to replace placeholder text
    result = service.documents().batchUpdate(
        documentId=document_id, body={'requests': requests}).execute()

# Close the cursor and the database connection
cur.close()
conn.close()
