import google.generativeai as genai
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
import requests
import os
import io

# 1. load file from google drive
# 2. send file to ocr api and get text (text extraction from images/pdfs) -- ocr.space
# 3. send user_data to ai api and get autofill data -- Google Gemini

def get_text_from_ocr(fh, file_name):
    ocr_url = "https://api.ocr.space/parse/image"
    payload = {
        "isOverlayRequired": "true",
        "apikey": "K84387269988957",
        "language": "eng",
    }

    fh.seek(0)  # Go back to beginning of file before reading
    files = { 'file': (file_name, fh)}

    print("🔎 Sending to OCR API...")
    r = requests.post(ocr_url, files=files, data=payload)
    response_json = r.json()
    doc_text = ""
    for line in response_json['ParsedResults'][0]['TextOverlay']['Lines']:
        doc_text += line['LineText'] + "\n"
    return doc_text



def get_file_from_drive_and_return_ocr_data(file_url):
    print('1. inside get file from drive and return ocr data....')
    # === Step 1: Google Drive Auth ===
    SERVICE_ACCOUNT_FILE = 'credential.json'
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    drive_service = build('drive', 'v3', credentials=creds)

    # === Step 2: Google Drive File ID ===
    # file_url = 'https://drive.google.com/file/d/1NkJpspv6FV_ouF9IW7N59m4OsdhI368T/view?usp=drive_link'
    file_id = file_url.split("id=")[1].split("&")[0] 
    print(file_url, file_id)

    # === Step 3: Download File into Memory ===
    request = drive_service.files().get_media(fileId=file_id)
    file_metadata = drive_service.files().get(fileId=file_id).execute()
    file_name = file_metadata['name']
    file_mime = file_metadata['mimeType']

    print(f"🔍 File Name: {file_name}")
    print(f"📄 MIME Type: {file_mime}")

    # Download the file content into memory
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"⬇️ Download progress: {int(status.progress() * 100)}%")
    ocr_result = get_text_from_ocr(fh, file_name)
    return ocr_result

    

def get_autofill_data(html_data, user_data):
    # fetch autofill data from ai api using html data and user data
    api_key = "AIzaSyC_OPZO2FLYsAs-Gtvjx-5AQGYKBDUul5k"
    api_input = f"Website Text: {html_data}\nuser json data: {user_data}"
    instructions ="I have provided website html data and user json, for each and every input field provide input name (in the format 'input[name='input_name']') or class name (it should be in the format '.class_name') or class id (it should be in the format '#class_id') of the field (if there are many class names only provide first class name ) as key and value as its relative user data. For non direct or descriptive field generate relevant response using user data and assign the value. Also follow order while giving the json, the order should be same as the elements from top to bottom. Only output list of json data with key as input html class name and value as user relevant data, don't give extra response except response list of json."
    
    user_prompt = api_input+ instructions   
    client = genai.configure(api_key=api_key)
    response = genai.GenerativeModel('gemini-2.0-flash').generate_content(user_prompt)

    autofillData = "".join(response.text.split('\n')[1:-1])
    print('1. Fetched auto fill data....')
    return autofillData


