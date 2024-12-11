import requests
import json


def get_location_id(api_key, latitude, longitude):
    try:
        url = f"https://dataservice.accuweather.com/locations/v1/cities/geoposition/search?apikey={api_key}&q={latitude},{longitude}"
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        data = response.json()
        if "Key" in data:
            return data["Key"]
        else:
            raise ValueError("Location key not found in response.")

    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"An unexpected error occurred: {e}"


def get_conditions(api_key, latitude, longitude):
    try:
        location_key = get_location_id(api_key, latitude, longitude)
        if isinstance(location_key, str) and location_key.startswith("Request error"):
            return location_key  # Return the error message from get_location_id

        url_1day = f"https://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}?apikey={api_key}&metric=true&details=true"
        url_current = f"https://dataservice.accuweather.com/currentconditions/v1/{location_key}?apikey={api_key}&details=true"

        response_1day = requests.get(url_1day)
        response_current = requests.get(url_current)
        response_1day.raise_for_status()
        response_current.raise_for_status()

        data_1day = response_1day.json()
        data_current = response_current.json()

        if not data_current or not data_1day.get("DailyForecasts"):
            raise ValueError("Invalid data received from API.")

        conditions = {
            "temperature": data_current[0]["Temperature"]["Metric"]["Value"],
            "humidity": data_current[0]["RelativeHumidity"],
            "wind": data_current[0]["Wind"]["Speed"]["Metric"]["Value"],
            "rain_probability_day": data_1day["DailyForecasts"][0]["Day"]["RainProbability"],
            "rain_probability_night": data_1day["DailyForecasts"][0]["Night"]["RainProbability"]
        }
        return conditions
    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"An unexpected error occurred: {e}"


def check_bad_weather(conditions):
    try:
        bad_weather_score = 0

        if conditions["rain_probability_day"] > 70 or conditions["rain_probability_night"] > 70:
            bad_weather_score += 1

        if conditions['temperature'] < 0 or conditions['temperature'] > 35:
            bad_weather_score += 1

        if conditions['wind'] > 15:
            bad_weather_score += 1

        if bad_weather_score >= 2:
            return "Неблагоприятные погодные условия"
        if bad_weather_score == 1:
            return "Слегка неблагоприятные погодные условия"
        if bad_weather_score == 0:
            return "Благоприятные погодные условия"
    except Exception as e:
        return f"An unexpected error occurred: {e}\nOutput: {conditions}"