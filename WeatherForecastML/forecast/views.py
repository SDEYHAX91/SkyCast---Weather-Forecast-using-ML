from django.shortcuts import render

# Create your views here.
import requests #for fetching data from API
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error
from datetime import datetime, timedelta
import pytz
import os

#OpenWeather API KEY
API_KEY = '7d95bae8446e44197407f72423e6b25e'
BASE_URL = 'https://api.openweathermap.org/data/2.5/'
#Base URL for making API Requests

"""
+----------------------------------+
|  1. Fetch Current Weather Data:  |
+----------------------------------+
"""
def get_current_weather(city):

    url = f"{BASE_URL}weather?q={city}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    data = response.json()

    # Invalid city or API error
    if response.status_code != 200:
        return {
            'error': True,
            'message': data.get('message', 'Unable to fetch weather data.')
        }

    return {
        'error': False,
        'city': data['name'],
        'country': data['sys']['country'],
        'current_temp': round(data['main']['temp']),
        'feels_like': round(data['main']['feels_like']),
        'temp_min': round(data['main']['temp_min']),
        'temp_max': round(data['main']['temp_max']),
        'pressure': round(data['main']['pressure']),
        'humidity': round(data['main']['humidity']),
        'wind_gust_dir': data['wind']['deg'],
        'WindGustSpeed': round(data['wind']['speed']),
        'description': data['weather'][0]['description'],
        'clouds': data['clouds']['all'],
        'visibility': round(data['visibility'] / 1000, 1)
    }
  
"""
+----------------------------------+
|  2. Get Historical Data:         |
+----------------------------------+
"""  
def read_hist_data(filename):

  df = pd.read_csv(filename)
  df.dropna()   #remove records with missing values
  df.drop_duplicates()  #remove records with diplicate data
  return df

"""
+----------------------------------+
|  3. Preprocess Data:             |
+----------------------------------+
"""
def prep_data(data):

  le = LabelEncoder()

  #transform categorical column into numerical....
  data['WindGustDir'] = le.fit_transform(data['WindGustDir'])
  data['RainTomorrow'] = le.fit_transform(data['RainTomorrow'])

  #define feature variables & target variables
  X = data[['MinTemp', 'MaxTemp', 'WindGustDir', 'WindGustSpeed',
            'Humidity', 'Pressure', 'Temp']]
  y = data['RainTomorrow']  #target label

  return X, y, le

"""
+---------------------------------------+
|  4. Train Rain Classification model:  |
+---------------------------------------+
"""
def train_rain_model(X, y):

  #Train-Test Split
  X_train, X_test, y_train, y_test = train_test_split(X, y,
                                                test_size=0.2, random_state=42)
  #Random Forest Classifier Model
  model = RandomForestClassifier(n_estimators=100, random_state=42)
  model.fit(X_train, y_train)

  y_pred = model.predict(X_test)

  accuracy = accuracy_score(y_test, y_pred)
  print(f"Accuracy: {round(accuracy,3)}")

  return model

"""
+----------------------------------+
|  5. Prepare Regression Data:     |
+----------------------------------+
"""
def prep_reg_data(data, feature):

  X, y = [], [] #initialize list for features & labels

  for i in range(len(data) - 1):
    X.append(data[feature].iloc[i])
    y.append(data[feature].iloc[i+1])

  X = np.array(X).reshape(-1, 1)
  y = np.array(y)

  return X, y

"""
+----------------------------------+
|  6. Train Regression Data:       |
+----------------------------------+
"""
def train_reg_model(X, y):

  model = RandomForestRegressor(n_estimators=100, random_state=42)
  model.fit(X, y)

  return model

"""
+----------------------------------+
|  7. Predict Future Data:         |
+----------------------------------+
"""
def predict_future(model, current_val):
  predictions = [current_val]

  for i in range(7):
    nxt_val = model.predict(np.array([[predictions[-1]]]))
    predictions.append(nxt_val[0])

  return predictions[1:]

"""
+----------------------------------+
|  8. Weather Analysis:            |
+----------------------------------+
"""
def weather_view(request):
    if request.method == 'POST':
        city = request.POST.get('city')
        current_weather = get_current_weather(city)
        if current_weather.get('error'):
          return render(
              request,
              'weather.html',
              {
                  'show_error': True,
                  'error_message': "City not found. Please enter a valid city name."
              }
        )
        weather_desc = current_weather['description'].lower()
        if weather_desc == "few clouds":
            weather_class = "few"
        elif weather_desc == "scattered clouds":
            weather_class = "scattered"
        else:
            weather_class = weather_desc.split()[0]  
        
        #load historical data
        csv_path = os.path.join('C:\PROJECTS\Weather ML\Data\weather.csv')
        hist_data = read_hist_data(csv_path)

        #prepare data & train model
        X, y, le = prep_data(hist_data)
        rain_model = train_rain_model(X, y)

        # Map wind direction to compass points
        wind_deg = current_weather['wind_gust_dir'] % 360
        compass_points = [
            ("N", 0, 11.25), ("NNE", 11.25, 33.75), ("NE", 33.75, 56.25),
            ("ENE", 56.25, 78.75), ("E", 78.75, 101.25), ("ESE", 101.25, 123.75),
            ("SE", 123.75, 146.25), ("SSE", 146.25, 168.75), ("S", 168.75, 191.25),
            ("SSW", 191.25, 213.75), ("SW", 213.75, 236.25), ("WSW", 236.25, 258.75),
            ("W", 258.75, 281.25), ("WNW", 281.25, 303.75), ("NW", 303.75, 326.25),
            ("NNW", 326.25, 348.75)]
        compass_direction = next(point for point, start,
                                end in compass_points if start <= wind_deg < end)

        compass_direction_encoded = le.transform(
            [compass_direction])[0] if compass_direction in le.classes_ else -1

        #prepare current weather data
        current_data = { 
            'MinTemp': current_weather['temp_min'],
            'MaxTemp': current_weather['temp_max'],
            'WindGustDir': compass_direction_encoded,
            'WindGustSpeed': current_weather['WindGustSpeed'],
            'Humidity': current_weather['humidity'],
            'Pressure': current_weather['pressure'],
            'Temp': current_weather['current_temp']}

        current_df = pd.DataFrame([current_data])

        #rain prediction
        rain_prediction = rain_model.predict(current_df)[0]

        #prepare regression model for temperature and humidity
        X_temp, y_temp = prep_reg_data(hist_data, 'MaxTemp')
        X_hum, y_hum = prep_reg_data(hist_data, 'Humidity')

        temp_model = train_reg_model(X_temp, y_temp)
        hum_model = train_reg_model(X_hum, y_hum)

        # predict future temperature & humidity (for 7 days)
        future_temp = predict_future(temp_model, current_data['Temp'])
        future_hum = predict_future(hum_model, current_data['Humidity'])

        #prepare time for future predictions (7 days)
        timezone = pytz.timezone('Asia/Kolkata')
        now = datetime.now(timezone)
        next_day = now + timedelta(days=1)
        next_day = next_day.replace(hour=12, minute=0, second=0, microsecond=0)  # Midday prediction

        future_times = [(next_day + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]

        #store each value seperately
        date1, date2, date3, date4, date5, date6, date7 = future_times
        temp1, temp2, temp3, temp4, temp5, temp6, temp7 = future_temp
        hum1, hum2, hum3, hum4, hum5, hum6, hum7 = future_hum
        
        #pass data to template
        context = {
        'location': city,
        'current_temp': current_weather['current_temp'],
        'MinTemp': current_weather['temp_min'],
        'MaxTemp': current_weather['temp_max'],
        'feels_like': current_weather['feels_like'],
        'humidity': current_weather['humidity'],
        'clouds': current_weather['clouds'],
        'description': current_weather['description'],
        'city': current_weather['city'],
        'country': current_weather['country'],
        'weather_class': weather_class,

        'time': datetime.now(),
        'date': datetime.now().strftime("%B %d, %Y"),

        'wind': current_weather['WindGustSpeed'],
        'pressure': current_weather['pressure'],
        'visibility': current_weather['visibility'],

        'date1': date1,
        'date2': date2,
        'date3': date3,
        'date4': date4,
        'date5': date5,
        'date6': date6,
        'date7': date7,
        
        'temp1': f"{round(temp1, 1)}",
        'temp2': f"{round(temp2, 1)}",
        'temp3': f"{round(temp3, 1)}",
        'temp4': f"{round(temp4, 1)}",
        'temp5': f"{round(temp5, 1)}",
        'temp6': f"{round(temp6, 1)}",
        'temp7': f"{round(temp7, 1)}",
        
        'hum1': f"{round(hum1, 1)}",
        'hum2': f"{round(hum2, 1)}",
        'hum3': f"{round(hum3, 1)}",
        'hum4': f"{round(hum4, 1)}",
        'hum5': f"{round(hum5, 1)}",
        'hum6': f"{round(hum6, 1)}",
        'hum7': f"{round(hum7, 1)}",
        }
        return render(request, 'weather.html', context)
    
    return render(request, 'weather.html')