from flask import Flask, request, render_template
import requests
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class LocationForm(FlaskForm):
    location_A = StringField('Введите название отправной точки:', validators=[DataRequired()])     # Поле для ввода названия отправной точки
    location_B = StringField('Введите название конечной точки:', validators=[DataRequired()])     # Поле для ввода названия конечной точки
    submit = SubmitField('Получить данные о погоде')     # Кнопка для отправки формы
API_KEY = 'VppSmk8M7Al00nYGHmj6HM48KqnFakVH'

app = Flask(__name__, template_folder=r'C:\Users\ilalc\PycharmProjects\PythonProject\templates', static_folder=r'C:\Users\ilalc\PycharmProjects\PythonProject\static')
app.config["SECRET_KEY"] = "oboldui123"

def check_bad_weather(wet_info: dict):
    '''Функция анализа погодных условий'''
    if wet_info['temperature_celsius'] < 0:
        return 'Температура ниже 0, советуем одеться потеплее'
    elif wet_info['temperature_celsius'] > 35:
        return 'Очень жарко, советуем оставаться дома или, если вы на улице оставайтесь в тени'
    elif wet_info['wind_speed'] > 7:
        return 'Сильный ветер, советуем оставаться дома, воизбежании несчастных случаев'
    elif wet_info['precipitation_probability'] > 70:
        return 'Высокая вероятность осадков, не забудьте захватить с собой зонтик'
    else:
        return 'Самое лучшее время для прогулки'


def req(city):
    """Получение кординат"""
    location_url = f'http://dataservice.accuweather.com/locations/v1/cities/search?apikey={API_KEY}&q={city}&language=ru'
    try:
        response = requests.get(location_url)
        data = response.json()
        if data:
            lat = data[0]['GeoPosition']['Latitude']
            long = data[0]['GeoPosition']['Longitude']
            return [lat, long]
    except requests.exceptions.RequestException as e:
        print(f'Ошибка запроса: {e}')
        return None


def get_loc_code_by_coords(city):
    """Функция для получения гео-ключа по кординатам"""
    city_cor = f'{city[0]},{city[1]}'
    location_url = f'http://dataservice.accuweather.com/locations/v1/cities/geoposition/search?apikey={API_KEY}&q={city_cor}'
    try:
        response = requests.get(location_url)
        data = response.json()
        if data:
            return [data['Key'], data['AdministrativeArea']['LocalizedName']]
    except requests.exceptions.RequestException as e:
        print(f'Ошибка запроса: {e}')
        return None


def get_weather_data(loc_key):
    '''Фукция получения данных о погоде'''
    weather_url = f'http://dataservice.accuweather.com/currentconditions/v1/{loc_key}?apikey={API_KEY}&details=true'  # запрос к api
    try:
        weather_r = requests.get(weather_url)  # гет-запрос к api
        weather_data = weather_r.json()[0]
        temperature_celsius = weather_data['Temperature']['Metric']['Value']
        humidity_percentage = weather_data['RelativeHumidity']
        wind_speed = round(weather_data['Wind']['Speed']['Metric']['Value'] * 0.2778, 2)
        precipitation_probability = 0 if not weather_data['HasPrecipitation'] else 100
        wet_info = {
            'temperature_celsius': temperature_celsius,
            'humidity_percentage': f'{humidity_percentage}%',
            'wind_speed': wind_speed,
            'precipitation_probability': precipitation_probability
        }
        return wet_info
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса погода: {e}")



@app.route("/", methods=['GET', 'POST'])
def main():
    form = LocationForm()
    analize = {}
    if request.method == "POST":  # Проверяем, был ли отправлен POST-запрос
        if form.validate_on_submit():  # Проверяем, что форма валидн
            point_A = form.location_A.data  # Получаем данные из поля location_A
            point_B = form.location_B.data # Получаем данные из поля location_B
            k_A = get_loc_code_by_coords(req(point_A))[0]  # Получаем код местоположения по координатам A
            k_B = get_loc_code_by_coords(req(point_B))[0] # Получаем код местоположения по координатам B
            response_A = get_weather_data(k_A)  # Получаем данные о погоде A
            response_B = get_weather_data(k_B)  # Получаем данные о погоде B
            analize_A = check_bad_weather(response_A)  # Анализируем данные о погоде A
            analize_B = check_bad_weather(response_B)  # Анализируем данные о погоде A
            weather_data = {
            f'Анализ погодных условий в городе: {point_A}':{
            'temperature_celsius': response_A['temperature_celsius'],
            'precipitation_probability': response_A['precipitation_probability'],
            'humidity_percentage': response_A['humidity_percentage'],
            'wind_speed': response_A['wind_speed'],
            'analyze': analize_A
            },

            f'Анализ погодных условий в городе: {point_B}':{
            'temperature_celsius': response_B['temperature_celsius'],
            'precipitation_probability': response_B['precipitation_probability'],
            'humidity_percentage': response_B['humidity_percentage'],
            'wind_speed': response_B['wind_speed'],
            'analyze': analize_B}
            }
            return render_template('weather.html', data=weather_data)  # Отображаем данные о погоде
    return render_template('main.html', form=form)  # Отображаем форму при GET-запросе


if __name__ == "__main__":
    app.run(debug=True)