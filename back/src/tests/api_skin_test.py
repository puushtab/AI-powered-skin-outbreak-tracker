import requests

url = 'http://localhost:8000/api/v1/skin-plan/generate'
payload = {
    "user_profile": {
        "gender": "female",
        "weight": 65.0,
        "dob": "1995-05-03"
    },
    "timeseries_data": {}  
}

response = requests.post(url, data=payload)

print(response.status_code)        # e.g. 200
print(response.text)               # server’s raw response
print(response.json())             # if the response is JSON
