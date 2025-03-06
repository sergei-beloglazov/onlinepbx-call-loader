import requests
import json
import os
from datetime import datetime, timedelta
from settings import apiKey, domain, recordsPath, logsPath

# Global variable to store authentication keys
auth_keys = {
    "key": None,
    "key_id": None
}

def log_message(message):
    """Logs a message to a file with a timestamp."""
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    log_filename = os.path.join(logsPath, datetime.now().strftime("%Y-%m-%d") + ".txt")
    with open(log_filename, "a") as log_file:
        log_file.write(f"{timestamp} {message}\n")

def authenticate():
    """Authenticates with the onlinePBX API and stores the keys in the global variable."""
    url = f"https://api.onlinepbx.ru/{domain}/auth.json"
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded'
    }
    payload = {
        'auth_key': apiKey,
        'new': 'true'
    }
    response = requests.post(url, headers=headers, data=payload)
    data = response.json()
    
    if data["status"] == "1":
        auth_keys["key"] = data["data"]["key"]
        auth_keys["key_id"] = data["data"]["key_id"]
        log_message("Authentication successful.")
        # log_message(f"Request payload: {payload}")
        # log_message(f"Response data: {data}")
    else:
        log_message(f"Authentication failed: {data['comment']}")
        log_message(f"Request payload: {payload}")
        log_message(f"Response data: {data}")
        raise Exception("Authentication failed")

def fetch_call_history(start_date, end_date):
    """Fetches call history from the onlinePBX API within the specified date range."""
    url = f"https://api.onlinepbx.ru/{domain}/mongo_history/search.json"
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'x-pbx-authentication': f"{auth_keys['key_id']}:{auth_keys['key']}"
    }
    payload = {
        'start_stamp_from': int(start_date.timestamp()),
        'start_stamp_to': int(end_date.timestamp())
    }
    response = requests.post(url, headers=headers, data=payload)
    data = response.json()
    
    if data["status"] == "1":
        log_message("Call history fetched successfully.")
        log_message(f"Response data: {data}")
        return data["data"]
    else:
        log_message(f"Failed to fetch call history: {data['comment']}")
        log_message(f"Request headers: {headers}")
        log_message(f"Request payload: {payload}")
        log_message(f"Response data: {data}")
        raise Exception("Failed to fetch call history")

def download_call_recordings(uuids):
    """Downloads call recordings for the given UUIDs."""
    url = f"https://api.onlinepbx.ru/{domain}/mongo_history/search.json"
    headers = {
        'accept': 'application/json',
        'content-type': 'application/x-www-form-urlencoded',
        'x-pbx-authentication': f"{auth_keys['key_id']}:{auth_keys['key']}"
    }
    payload = {
        'uuid_array': ','.join(uuids),
        'download': 'true'
    }
    response = requests.post(url, headers=headers, data=payload)
    data = response.json()
    
    if data["status"] == "1":
        download_url = data["data"]
        log_message(f"Downloading call recordings from {download_url}")
        response = requests.get(download_url)
        # Generate the filename with the current date and time
        base_filename = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(recordsPath, f"{base_filename}.tar")
        
        # Check if the file already exists and add a counter if necessary
        counter = 1
        while os.path.exists(filename):
            filename = os.path.join(recordsPath, f"{base_filename}({counter}).tar")
            counter += 1
            if counter > 999999:
                raise Exception("Unable to save file: too many files with the same download time.")
        with open(filename, "wb") as file:
            file.write(response.content)
        log_message(f"Call recordings downloaded successfully to file {filename}.")
    else:
        log_message(f"Failed to download call recordings: {data['comment']}")
        log_message(f"Request payload: {payload}")
        log_message(f"Response data: {data}")
        raise Exception("Failed to download call recordings")

def main():
    try:
        authenticate()
        # Get the call history for the last 30 days
        end_date = datetime.now().replace(hour=23, minute=59, second=59)
        start_date = end_date - timedelta(days=30)
        log_message(f"Fetching calls for the period from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        call_history = fetch_call_history(start_date, end_date)
        uuids = [call["uuid"] for call in call_history]
        download_call_recordings(uuids)
    except Exception as e:
        log_message(f"Error: {str(e)}")

if __name__ == "__main__":
    main()