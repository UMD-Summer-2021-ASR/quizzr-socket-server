# Quizzr Socket Server

## Installation
1. Clone this repository into a python 3.8 virtual environment
2. Run `pip install -r requirements.txt` in the console/terminal
3. Generate a firebase admin secrets json in the firebase
   - Login to firebase using the Quizzr gmail
   - Click on the Settings > "Project settings" button in the left navigation bar
   - Go to the Service accounts tab
   - Go to the Firebase Admin SDK tab
   - Click Generate new private key
4. Configure environment variables
   1. Get the file path of the firebase admin secrets json and set the 'GOOGLE_APPLICATION_CREDENTIALS' environment variable to that path using `export GOOGLE_APPLICATION_CREDENTIALS="<your json path>"`
   2. Set the 'HLS_HANDSHAKE' environment variable to the handshake set in the HLS server using `export HLS_HANDSHAKE="<your HLS handshake>"`
   3. Set the 'BACKEND_URL' environment variable to the data flow URL
   4. Set the 'HLS_URL' environment variable to the HLS server URL
5. Run `main.py` using `python main.py`
