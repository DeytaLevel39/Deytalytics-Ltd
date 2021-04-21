from typing import Optional,List

from bson import ObjectId
from fastapi import FastAPI, Body
from fastapi.encoders import jsonable_encoder
import requests, json
from pydantic import BaseModel, HttpUrl, constr, confloat
from genson import SchemaBuilder
import pymongo

from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def mongo_cnt(password, myFirstDatabase):
    mongo_cntstr = "mongodb+srv://admin:"+password+"@cluster0.jbbpl.mongodb.net/"+myFirstDatabase+"?retryWrites=true&w=majority"
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


def ResponseModel(data, message):
    return {
        "data": [data],
        "code": 200,
        "message": message,
    }

def ErrorResponseModel(error, code, message):
    return {"error": error, "code": code, "message": message}

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
    GeoLocation: Optional [geolocation] = None

class business_card(BaseModel):
    firstname: str
    lastname: str
    jobtitle: str
    mobile: str
    linkedin: HttpUrl
    github: Optional [HttpUrl] = None
    website: Optional [HttpUrl] = None
    location: location_info

class business_card_with_id(BaseModel):
    id: str
    firstname: str
    lastname: str
    jobtitle: str
    mobile: str
    linkedin: HttpUrl
    github: Optional [HttpUrl] = None
    website: Optional [HttpUrl] = None
    location: location_info

@app.get("/", response_class=HTMLResponse)
async def root():
    homepage = """
<!DOCTYPE html>
<html lang="en">
<head>
  <title>Business Card</title>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://www.dtsquared.co.uk/wp-content/cache/autoptimize/css/autoptimize_5691c34ca4ff6ee715f4ada0c136a9f2.css">
  <link rel="stylesheet" href="static/typewriter.css">
  <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.16.0/umd/popper.min.js"></script>
  <script src="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
</head>
<body>

<div class="c-main">  
<div class="o-container" style="background-repeat: no-repeat; background-size: cover; background-image: url('static/background-cover.png');">
  <div class="c-hero-grid row">
    <div class="c-hero__grid__txt">
    <div class="typewriter">
      <h2>&nbsp</h2>
      <h1 class="c-txt--h3" style="color:#fe911b;">JAMES DEY</h1></div>
      <h2 class="c-txt--h4">Data Architect</h2>
      <table>
      <tr><td class = "c-txt--h4"><img src="https://img.icons8.com/material-two-tone/2x/phone.png"></td><td style="text-align: left;">+447941252447</td></tr>
      <tr><td class = "c-txt--h4"><img src="https://img.icons8.com/fluent-systems-regular/2x/email-open.png"</td><td style="text-align: left;">james_dey@hotmail.com</td></tr>
      <tr><td class = "c-txt--h4"><img src="https://img.icons8.com/material-rounded/2x/domain--v2.png"></td><td style="text-align: left;"><a href="https://deytaflask.herokuapp.com">https://deytaflask.herokuapp.com</a></td></tr>
      <tr><td class = "c-txt--h4"><img src="https://img.icons8.com/fluent-systems-regular/2x/linkedin.png"></td><td style="text-align: left;"><a href="https://www.linkedin.com/in/dataarchitectlondon">https://www.linkedin.com/in/dataarchitectlondon</a></td></tr>
      <tr><td class = "c-txt--h4"><img src="https://img.icons8.com/fluent-systems-regular/2x/github.png"></td><td style="text-align: left;"><a href="https://github.com/Deytalytics-JamesDey">https://github.com/Deytalytics-JamesDey</a></td></tr>
      <tr><td class = "c-txt--h4">REST API:</td><td style="text-align: left;"><a href="https://deytabizcard.herokuapp.com/businesscard?fname=James&lname=Dey">https://deytabizcard.herokuapp.com/businesscard</a></td></tr>
      </table>
    </div>
  </div>
</div>
</div>

</body>
</html>
"""

    return homepage

@app.get("/businesscard", response_model=business_card_with_id)
def businesscard(fname, lname):
    coll = db['businesscards']
    bcard_json = coll.find_one({"firstname":fname,"lastname":lname})
    if bcard_json: bcard_json["id"] = str(bcard_json["_id"])
    return bcard_json

@app.post("/", response_description="Business card added in to the database")
async def add_bizcard(bizcard_data: business_card = Body(...)):
    coll = db['businesscards']
    bizcard = coll.insert_one(jsonable_encoder(bizcard_data))
    new_bizcard = coll.find_one(bizcard.inserted_id,{"_id":0})
    new_bizcard["id"]=str(bizcard.inserted_id)
    return (ResponseModel(new_bizcard,"Business card added successfully"))

@app.delete("/{id}", response_description="Business card deleted from the database")
async def delete_bizcard_data(id: str):
    coll = db['businesscards']
    if len(id)!= 24:
        return ErrorResponseModel(
            "An error occurred", 404, "Business card with id {0} needs to be a 24 byte string".format(id)
        )
    bizcard = coll.find_one({"_id": ObjectId(id)})
    if bizcard:
        deleted_bizcard = coll.delete_one({"_id":ObjectId(id)})
        if deleted_bizcard:
            return ResponseModel(
                "Business card with ID: {} removed".format(id), "Business card deleted successfully"
            )
    return ErrorResponseModel(
        "An error occurred", 404, "Business card with id {0} doesn't exist".format(id)
    )

#Ok connect to our mongodb Atlas cluster
db = mongo_cnt("openbanking", "businesscard")