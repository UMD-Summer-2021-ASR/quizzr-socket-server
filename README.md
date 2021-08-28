# Quizzr Socket Server

## Installation
1. Clone this repository
2. Run `pip install -r requirements.txt` in the console/terminal
3. Generate a firebase admin secrets json in the firebase
   - Login to firebase using the Quizzr gmail
   - Click on the Settings > "Project settings" button in the left navigation bar
   - Go to the Service accounts tab
   - Go to the Firebase Admin SDK tab
   - Click Generate new private key
4. Get the file path of the json file and replace the 'GOOGLE_APPLICATION_CREDENTIALS' environment variable's value with that path in `main.py`
5. Run `main.py`