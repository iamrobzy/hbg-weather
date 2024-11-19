import modal

app = modal.App('scheduler')

@app.function(schedule=modal.Period(seconds=10))
def update():
    print('Updating...')
    
    # Send dataframe to Streamlit frontend
    

@app.function()
def predict():
    
    # Extract features

    # Run model

    print('Predicting...')


"""
project = hopsworks.login(project=project_name, api_key_value=api_key)
fs = project.get_feature_store() 
secrets = util.secrets_api(project.name)

AQI_API_KEY = secrets.get_secret("AQI_API_KEY").value
location_str = secrets.get_secret("SENSOR_LOCATION_JSON").value
location = json.loads(location_str)

country=location['country']
city=location['city']
street=location['street']
aqicn_url=location['aqicn_url']
latitude=location['latitude']
longitude=location['longitude']

today = datetime.date.today()

# Retrieve feature groups
air_quality_fg = fs.get_feature_group(
    name='air_quality',
    version=1,
)
"""