from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from google.cloud import storage
import aiofiles
import firebase_admin
from firebase_admin import credentials
import pyrebase


cred = credentials.Certificate('/Users/apple/Downloads/xytech-test-firebase-adminsdk-9e882-31a2ff44b5.json')
firebase_admin.initialize_app(cred)

config = {
  "apiKey": "AIzaSyBxJEPJNiStVHfO8stAUIpBvceFTVzESDA",
  "authDomain": "xytech-test.firebaseapp.com",
  "databaseURL": "https://xytech-test-default-rtdb.firebaseio.com",
  "storageBucket": "xytech-test.appspot.com"
}

firebase = pyrebase.initialize_app(config)
storage = firebase.storage()
app = FastAPI()

# define the FastAPI endpoint to upload a file
@app.post('/upload')
async def upload_file(payload: UploadFile):
    # authenticate the file by checking its extension
    allowed_extensions = {'png', 'jpg', 'jpeg','pdf', 'txt'}
    file_extension = payload.filename.split('.')[-1]
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File type not supported")

    storage.child("uploads/" + payload.filename).put(payload.file)

    return {"filename": payload.filename}
    

    
    


