from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from google.cloud import storage
import aiofiles
import firebase_admin 
from firebase_admin import credentials

cred = credentials.Certificate('/Users/apple/Downloads/xytech-test-firebase-adminsdk-9e882-c2dbc87811.json')
firebase_admin.initialize_app(cred)

app = FastAPI()

# define the request payload using pydantic BaseModel
class FilePayload(BaseModel):
    file: UploadFile

# initialize the Firebase Storage client
client = storage.Client.from_service_account_json('/Users/apple/Downloads/xytech-test-firebase-adminsdk-9e882-c2dbc87811.json')
bucket = client.get_bucket('xytech-test.appspot.com')

# define the FastAPI endpoint to upload a file
@app.post('/upload')
async def upload_file(payload: UploadFile):
    # authenticate the file by checking its extension
    allowed_extensions = {'png', 'jpg', 'jpeg','pdf', 'txt'}
    file_extension = payload.filename.split('.')[-1]
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File type not supported")

    with open(payload.filename, "wb") as f:
        contents = await payload.read()
        f.write(contents)
    return {"filename": payload.filename}

    # save the file to Firebase Storage
    # blob = bucket.blob(payload.file.filename)
    # blob.upload_from_string(await payload.file.read(), content_type=payload.file.content_type)

    # return a success message
    return {"message": "File uploaded successfully"}


