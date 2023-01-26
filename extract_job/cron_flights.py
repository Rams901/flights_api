import pygsheets
import json
import pandas as pd
import datetime
import requests
import itertools
import time

# Convert response to df
def convert_to_df(url, dep, dest, date_dep, date_arr):
  
  headers = {
       'Accept': 'application/json',
       'x-api-key' : "prtl6749387986743898559646983194"
            }

  data = { "query": {

    "market": "US",
    "locale": "en-US",
    "currency": "CAD",
    "queryLegs": [{"originPlaceId" : {"iata": dep}, "destinationPlaceId" : {"iata": dest}, "date": {"year": 2023, "month": date_dep, "day": 15}}],
"cabinClass": "CABIN_CLASS_BUSINESS",
"adults": 1
}
}

  checkpoint_url = "https://partners.api.skyscanner.net/apiservices/v3/flights/live/itineraryrefresh/create"
  # Start the search session
  response = requests.post(url,json = data, headers = headers)
  print(response.text)
  mp = json.loads(response.content)
  global_df = pd.DataFrame(columns = ['leg_id', 'price', 'operatingCarrierIds', 'marketingCarrierIds', 'originPlaceId', 'destinationPlaceId','agent', 'departureDateTime',  'arrivalDateTime','durationInMinutes', 'stopCount', 'url','segmentIds'])
  # restart if there is an error
  while ( 'code' in mp.keys()):
    response = requests.post(url,json = data, headers = headers)
    print(response.text)
    mp = json.loads(response.content)
  
  df = pd.DataFrame(mp)
  results = df.iloc[0:1]

  session_id = mp['sessionToken']
  print(session_id)
  legs_checkpoint = pd.DataFrame(results['content'].values[0]['legs']).columns
  
  body_checkpoint = {
      "itineraryId": legs_checkpoint[0]
  }

  # Wait till search finishes (since their doing it for each leg, it must be each leg having it's own different stuff)
  for leg in legs_checkpoint:
        body_checkpoint = {
          "itineraryId": leg
          }
        response = requests.post(checkpoint_url+'/'+session_id, json = body_checkpoint, headers = headers)
        mp = json.loads(response.content)
        while ( 'code' in mp.keys()):
            response = requests.post(checkpoint_url+'/'+session_id, json = body_checkpoint, headers = headers)
            mp = json.loads(response.content)

        while (mp['status'] == "RESULT_STATUS_INCOMPLETE"):
          response = requests.post(checkpoint_url+'/'+session_id, json = body_checkpoint, headers = headers)
          mp = json.loads(response.content)
          print(mp)
          time.sleep(0.5)
        
        df = pd.DataFrame(mp)
        results = df.iloc[0:1]
        
        interaries = pd.DataFrame(results['content'].values[0]['itineraries'])
        itineraries = interaries.T
        
        places = pd.DataFrame(results['content'].values[0]['places'])
        segments = pd.DataFrame(results['content'].values[0]['segments'])
        
        alliances = pd.DataFrame(results['content'].values[0]['alliances'])
        agents = pd.DataFrame(results['content'].values[0]['agents'])
        
        carriers = pd.DataFrame(results['content'].values[0]['carriers'])
        print(carriers.columns, carriers.values)
        legs = pd.DataFrame(results['content'].values[0]['legs'])
      # Status is either Unspecified or Complete
        df = pd.DataFrame(list(itertools.chain.from_iterable((itineraries['pricingOptions'].apply(lambda x: [{"price":f"{x[i]['price']['amount']}$", "agent":f"{agents[x[i]['agentIds'][0]].iloc[0]}", "url":f"{x[i]['items'][0]['deepLink']}", } for i in range(len(x))]).values))))
        

       
        reverse_legs = legs.T
        reverse_legs['originPlaceId'] = reverse_legs['originPlaceId'].apply(lambda x: places[x].values[2])
        reverse_legs['destinationPlaceId'] = reverse_legs['destinationPlaceId'].apply(lambda x: places[x].values[2])
        reverse_legs['marketingCarrierIds'] = reverse_legs['marketingCarrierIds'].apply(lambda x: carriers[x].iloc[0].values[0] if (len(carriers.columns) > 1) else carriers[x].iloc[-1].values[0])
        reverse_legs['operatingCarrierIds'] = reverse_legs['operatingCarrierIds'].apply(lambda x: carriers[x].iloc[0].values[0] if (len(carriers.columns) > 1) else carriers[x].iloc[-1].values[0])
        reverse_legs['leg_id'] = leg
        reverse_legs['arrivalDateTime'] = reverse_legs['arrivalDateTime'].apply(lambda x: datetime.datetime(year = x['year'], month = x['month'], day = x['day'], hour = x['hour'], minute = x['minute'], second = x['second']))
        reverse_legs['departureDateTime'] = reverse_legs['departureDateTime'].apply(lambda x: datetime.datetime(year = x['year'], month = x['month'], day = x['day'], hour = x['hour'], minute = x['minute'], second = x['second']))

        df['leg_id'] = leg
        local_df = pd.concat((df, reverse_legs), axis = 1)
        local_df = pd.merge(reverse_legs, df, on="leg_id")[['leg_id', 'price', 'operatingCarrierIds', 'marketingCarrierIds', 'originPlaceId', 'destinationPlaceId','agent', 'departureDateTime',  'arrivalDateTime','durationInMinutes', 'stopCount', 'url','segmentIds']]
        global_df = pd.concat((global_df, local_df), ignore_index = True)

  return global_df


class flights_Model():
  
  def __init__(self):
    
    spreadsheet_id = '1VKGTPvoy_57aAFlKRgaBb_g4Y2OzwOnJz78Dggmjb_U'
    gc = pygsheets.authorize(service_file = 'credentials.json')
    
    sh = gc.open_by_key(spreadsheet_id)
    self.worksheet = sh.worksheet_by_title("cleaned_flights")
    
    
  def start_job(self):
    
    try:
      updated_df = convert_to_df("https://partners.api.skyscanner.net/apiservices/v3/flights/live/search/create", 'YVR', 'BKK', 11, 12)
    except:
      updated_df = convert_to_df("https://partners.api.skyscanner.net/apiservices/v3/flights/live/search/create", 'YVR', 'BKK', 11, 12)
      
    df = self.worksheet.get_as_df()
    self.worksheet.set_dataframe(updated_df, start = (len(df), 1), extend = True, copy_head= False)
    
    return  len(updated_df)

model = flights_Model()
        
def get_model():
    return model

# Append the dataframe to the sheet

