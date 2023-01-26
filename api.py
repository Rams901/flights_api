from typing import Dict
from fastapi import Depends, FastAPI
from pydantic import BaseModel
import os
from fastapi.middleware.cors import CORSMiddleware
from typing import List

print(os.getcwd())
from extract_job.cron_flights import flights_Model, get_model


app = FastAPI()


origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#For now, it's just the daily cron, that can be triggered by a post trigger to start working
#Can add a limit for how many rows to change, using -1
class flightRequest(BaseModel):
    dep: str
    arr: str

class flightResponse(BaseModel):
    count: int
    

@app.post("/run_flight", response_model= flightResponse)
def flight(request: flightRequest, model: flights_Model = Depends(get_model)):
    print(request)
    count = model.start_job()
    
    return flightResponse(
       
        count = count
    )
