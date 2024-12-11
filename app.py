from flask import Flask, request, render_template
import requests
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

API_KEY = 'VppSmk8M7Al00nYGHmj6HM48KqnFakVH'

class LocationForm(FlaskForm):
    location_A = StringField('Введите название отправной точки:', validators=[DataRequired()])
    location_B = StringField('Введите название конечной точки:', validators=[DataRequired()])
    submit = SubmitField('Получить данные о погоде')

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config["SECRET_KEY"] = "oboldui123"

def analyze_weather_conditions(weather_info):
    """Анализирует погодные условия и возвращает рекомендации."""
    print("Анализируем погодные условия:", weather_info)  # Отладочное сообщение

    temperature = weather_info.get('temperature_celsius')
    wind_speed = weather_info.get('wind_speed')
    precipitation_probability = weather_info.get('precipitation_probability')

    if temperature is None or wind_speed is None or precipitation_probability is None:
        return 'Ошибка: недостаточно данных для анализа погоды.'

    if temperature < 0:
        return 'Температура ниже 0, советуем одеться потеплее.'
    elif temperature > 35:
        return 'Очень жарко, советуем оставаться дома или, если вы на улице, оставайтесь в тени.'
    elif wind_speed > 7:
        return 'Сильный ветер, советуем оставаться дома, во избежание несчастных случаев.'
    elif precipitation_probability > 70:
        return 'Высокая вероятность осадков, не забудьте захватить с собой зонтик.'
    else:
        return 'Самое лучшее время для прогулки.'

def get_coordinates(city):
    """Получает координаты города."""
    location_url = f'http://dataservice.accuweather.com/locations/v1/cities/search?apikey={API_KEY}&q={city}&language=ru'
    try:
        response = requests.get(location_url)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]['GeoPosition']['Latitude'], data[0]['GeoPosition']['Longitude']
    except requests.exceptions.RequestException as e:
        print(f'Ошибка запроса: {e}')
        return None

def get_location_key_by_coordinates(coordinates):
    """Получает гео-ключ по координатам."""
    lat, long = coordinates
    location_url = f'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search?apikey={API_KEY}&q={lat},{long}'
    try:
        response = requests.get(location_url)
        response.raise_for_status()
        data = response.json()
        if data:
            return [data['Key'], data['AdministrativeArea']['LocalizedName']]
    except requests.exceptions.RequestException as e:
        print(f'Ошибка запроса: {e}')
        return None

def get_weather_data(location_key):
    """Получает данные о погоде по гео-ключу."""
    weather_url = f'http://dataservice.accuweather.com/currentconditions/v1/{location_key}?apikey={API_KEY}&details=true'
    try:
        response = requests.get(weather_url)
        response.raise_for_status()
        weather_data = response.json()[0]
        return {
            'temperature_celsius': weather_data['Temperature']['Metric']['Value'],
            'humidity_percentage': f"{weather_data['RelativeHumidity']}%",
            'wind_speed': round(weather_data['Wind']['Speed']['Metric']['Value'] * 0.2778, 2),
            'precipitation_probability': 100 if weather_data['HasPrecipitation'] else 0
        }
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса погоды: {e}")
        return None

@app.route("/", methods=['GET', 'POST'])
def main():
    form = LocationForm()
    if form.validate_on_submit():
        point_A = form.location_A.data
        point_B = form.location_B.data

        # Получаем координаты по названиям городов
        coords_A = get_coordinates(point_A)
        coords_B = get_coordinates(point_B)

        if coords_A and coords_B:
            # Получаем локальные ключи по координатам
            loc_key_A = get_location_key_by_coordinates(coords_A)
            loc_key_B = get_location_key_by_coordinates(coords_B)

            if loc_key_A and loc_key_B:
                # Получаем данные о погоде по локальным ключам
                weather_A = get_weather_data(loc_key_A[0])
                weather_B = get_weather_data(loc_key_B[0])

                if weather_A and weather_B:
                    # Анализируем погодные условия
                    analysis_A = analyze_weather_conditions(weather_A)
                    analysis_B = analyze_weather_conditions(weather_B)
                    print(analysis_A)
                    # Формируем данные для отображения
                    weather_data = {
                        f'Анализ погодных условий в городе: {point_A}': {
                            'temperature_celsius': weather_A['temperature_celsius'],
                            'precipitation_probability': weather_A['precipitation_probability'],
                            'humidity_percentage': weather_A['humidity_percentage'],
                            'wind_speed': weather_A['wind_speed'],
                            'analysis': analysis_A
                        },
                        f'Анализ погодных условий в городе: {point_B}': {
                            'temperature_celsius': weather_B['temperature_celsius'],
                            'precipitation_probability': weather_B['precipitation_probability'],
                            'humidity_percentage': weather_B['humidity_percentage'],
                            'wind_speed': weather_B['wind_speed'],
                            'analysis': analysis_B
                        }
                    }
                    # Здесь вы можете передать weather_data в шаблон для отображения
                    return render_template('weather.html', data=weather_data)

    return render_template('main.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)