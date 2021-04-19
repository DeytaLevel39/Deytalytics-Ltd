from typing import Optional,List
from fastapi import FastAPI
import requests, json
from pydantic import BaseModel, HttpUrl, constr, confloat
from genson import SchemaBuilder
import pymongo


app = FastAPI()

def mongo_cnt(password, myFirstDatabase):
    mongo_cntstr = "mongodb+srv://admin:"+password+"@cluster0.jbbpl.mongodb.net/"+myFirstDatabase+"?retryWrites=true&w=majority"
    print(mongo_cntstr)
    client = pymongo.MongoClient(mongo_cntstr)
    db = client.test
    return db


def fetch_ob_urls():

    opendata_github_url="https://raw.githubusercontent.com/OpenBankingUK/opendata-api-spec-compiled/master/participant_store.json"

    resp = requests.get(opendata_github_url)

    urls = []

    if resp.status_code == 200:
        resp_json = resp.json()
        for d in resp_json['data']:
            base_url = d['baseUrl']
            for api in d['supportedAPIs']:
                if 'business-current-accounts' in d['supportedAPIs']:
                    api_version=d['supportedAPIs']['business-current-accounts']
                    append_str = [base_url+"/"+api_version[0]+"/"+api,api]
                    urls.append(append_str)
    else:
        print("Failed to receive participant list")

    return (urls)

#Ok connect to our mongodb Atlas cluster
db = mongo_cnt("openbanking", "businesscard")


# Data models
class msg(BaseModel):
    message: str

class geocoords(BaseModel):
    latitude: confloat(gt=-180, lt=180)
    longitude: confloat(gt=-180,lt=180)

class geolocation(BaseModel):
    GeographicCoordinates: geocoords

class location_info (BaseModel):
    city: str
    country: str
    ISOCountryCode: constr(max_length=3, min_length=3)
    GeoLocation: geolocation

class business_card(BaseModel):
    firstname: str
    lastname: str
    title: str
    mobile: str
    linkedin: HttpUrl
    location: location_info

@app.get("/", response_model=msg)
async def root():
    return {"message": "Hey there, this isn't the business card. Try putting /businesscard at the end of your request URL"}

@app.get("/businesscard", response_model=business_card)
def businesscard():
    bcard_json = {
 "firstname": "James",
 "lastname": "Dey",
 "title": "Data Architect",
 "mobile": "+447941252447",
 "linkedin": "https://www.linkedin.com/in/dataarchitectlondon/",
 "location": {
	        "city": "London",
	        "country": "United Kingdom",
                       "ISOCountryCode":"GBR",
                       "GeoLocation": {
			       "GeographicCoordinates": {
				"latitude": "51.4224864",
				"longitude": "-0.1884645"
			                   }
		                     }
	         }
}
    return bcard_json
