import json
from fastapi import FastAPI, File,HTTPException, UploadFile
import pandas as pd
import PyPDF3
import tabula
import time
import firebase_admin
import pyrebase
from firebase_admin import credentials
from google.cloud import storage
import tqdm
import numpy as np


app = FastAPI()

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
pdf_reader = PyPDF3.PdfFileReader(open('/Users/apple/Documents/GitHub/pdf_extraction/assets/Account Statement.pdf', 'rb'))

class Table:
    def __init__(self, page_num, table_num, data):
        self.page_num = page_num
        self.table_num = table_num
        self.data = data


@app.post("/extract_tables")
async def extract_tables(file: UploadFile = File(...), password: str = None):
    start_time = time.time()
    allowed_extensions = {'pdf', 'txt','csv','xslv'}
    file_extension = file.filename.split('.')[-1]
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="File type not supported")
    
    storage.child("uploads/" + file.filename).put(file.file)

    # Open the PDF file
    pdf_reader = PyPDF3.PdfFileReader(file.file)
    print("---- %s seconds for reading pdf" % (time.time() - start_time))

    # Decrypt the PDF with the password if provided
    if password and pdf_reader.isEncrypted:
        start_time = time.time()
        pdf_reader.decrypt(password)
        print("---- %s seconds for decrypting pass" % (time.time() - start_time))

    start_time = time.time()
    # Get the number of pages in the PDF
    num_pages = pdf_reader.getNumPages()

    dfs = []
    
    # Extract tables from all pages using tabula-py
    for page_num in tqdm.tqdm(range(1, num_pages + 1)):
        tables = tabula.read_pdf(
            file.file,
            pages=page_num,
            password=password,
            area="all",
            relative_area=True,
            stream=True,
            lattice=True,
            pandas_options={"header": None},
            guess=False,
        )
        for table in tables:
            dfs.append(pd.DataFrame(table))

    # Combine all tables into one data frame
    if dfs:
        df = pd.concat(dfs)
        header = df.iloc[0]
        df = df[1:]
        df.columns = header
        pattern = r'^\s*(Date|Details|Ref\sNo\.\/Cheque\sNo|Debit|Credit|Balance)\s*$'
        mask = df.apply(lambda x: x.astype(str).str.contains(pattern).any(), axis=1)
        df = df[~mask]
        nmask = df['Details'].str.contains('UPI')
        nan_mask = df['Details'].isna()
        combined_mask = nmask & ~nan_mask
        df.loc[combined_mask, 'Details'] = 'Transfer From UPI'
        nemask = df['Details'].str.contains('NEFT')
        necombined_mask = nemask & ~nan_mask
        df.loc[necombined_mask, 'Details'] = 'Transfer From NEFT'
        Imask = df['Details'].str.contains('IMPS')
        Icombined_mask = Imask & ~nan_mask
        df.loc[Icombined_mask, 'Details'] = 'Transfer From IMPS'
        df["Debit"] = pd.to_numeric(df["Debit"], errors="coerce")  # convert string values to numeric values
        df["Debit"] = df["Debit"].fillna(0)  # replace NaN values with 0
        df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce")  # convert string values to numeric values
        df["Credit"] = df["Credit"].fillna(0)  # replace NaN values with 0
        df["Roundoff"] = np.ceil(df["Debit"] / 20) * 20
        df["RoundOff_amount"] = (df["Roundoff"] - df["Debit"])
        df["Returns"] = (df["RoundOff_amount"]*7)/100
        Total_RoundOff = df['RoundOff_amount'].sum()
        Total_returns = df['Returns'].sum()
    else:
        df = pd.DataFrame()

    # Convert the data frame to a JSON response
    return {
        "transactions": json.loads(df.to_json(orient='records')),
        "analysis": {
            "total_Roundoff": Total_RoundOff,
            "total_Returns": Total_returns,
        }
    }
    
    

     
   

   