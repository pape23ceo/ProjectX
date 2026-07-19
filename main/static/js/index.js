const canvas = document.getElementById('myCanvasChart');
const ctx = canvas.getContext('2d');

// collection
const WEATHER_CONDITIONS = {
    "clearsky_day": "Clear sky (Sunny)",
    "clearsky_night": "Clear sky",
    "partlycloudy_day": "Partly cloudy",
    "partlycloudy_night": "Partly cloudy",
    "cloudy": "Cloudy",
    "lightrainshowers_day": "Light rain showers",
    "rainshowers_day": "Rain showers",
    "heavyrainshowers_day": "Heavy rain showers",
    "lightrain": "Light rain",
    "rain": "Rain",
    "heavyrain": "Heavy rain",
    "lightssnowshowers_day": "Light snow showers",
    "snowshowers_day": "Snow showers",
    "heavysnowshowers_day": "Heavy snow showers",
    "lightsnow": "Light snow",
    "snow": "Snow",
    "heavysnow": "Heavy snow",
    "fog": "Foggy",
    "sleet": "Sleet",
    "lightsleet": "Light sleet",
    "heavysleet": "Heavy sleet",
    "sleetshowers_day": "Sleet showers",
    "lightssleetshowers_day": "Light sleet showers",
    "heavysleetshowers_day": "Heavy sleet showers",
    "thunderstorms": "Thunderstorms",
    "lightrainshowersandthunder_day": "Light rain showers and thunder",
    "rainandthunder": "Rain and thunder",
    "heavyrainandthunder": "Heavy rain and thunder",
    "fair_day": "Fair (Sunny)",
}

// define the value for weather data
const jsonElement = document.getElementById('json-weather-data');
const weatherData = JSON.parse(jsonElement.textContent);
const timeseries = weatherData.properties.timeseries;
const temp = timeseries[0].data.instant.details.air_temperature;
const humidity = timeseries[0].data.instant.details.relative_humidity;
const windSpeed = timeseries[0].data.instant.details.wind_speed;
const next1 = timeseries[0]?.data?.next_1_hours ?? {};
const symbol_code = next1?.summary?.symbol_code;
const weather_discrption = document.getElementById('weather_discription');
weather_discrption.textContent = WEATHER_CONDITIONS[symbol_code] ?? "Unknown";

const temp24h = timeseries
    .slice(0, Math.min(24, timeseries.length))
    .map(item => item.data.instant.details.air_temperature);
const temperatures = temp24h.slice(0, 7);

function getNextHours(count, includeCurrentHour = false) {
    const now = new Date();
    const currentHour = now.getHours();


    let startHour = currentHour;
    if (!includeCurrentHour) {

        startHour = currentHour + 1;
    }


    const start = new Date(now);
    start.setHours(startHour, 0, 0, 0);

    const hours = [];
    for (let i = 0; i < count; i++) {
        const h = new Date(start);
        h.setHours(start.getHours() + i);

        const hourStr = String(h.getHours()).padStart(2, '0') + ':00';
        hours.push(hourStr);
    }
    return hours;
}

const hours = getNextHours(7, false);

let chartWidth, chartHeight, paddingX, paddingY, maxDataValue, minDataValue;
let animationId = null;
function feelsLikeTemperature(temperature, humidity, windSpeed) {
    // Return null when temperature is missing, matching Python's None behavior
    if (temperature == null) return null;

    // Convert Celsius to Fahrenheit for use in the formulas
    const tempF = (temperature * 9) / 5 + 32;

    // Heat index (applies at high temperatures, requires humidity)
    if (temperature >= 27 && humidity != null) {
        const hi =
            -42.379 +
            2.04901523 * tempF +
            10.14333127 * humidity -
            0.22475541 * tempF * humidity -
            0.00683783 * tempF ** 2 -
            0.05481717 * humidity ** 2 +
            0.00122874 * tempF ** 2 * humidity +
            0.00085282 * tempF * humidity ** 2 -
            0.00000199 * tempF ** 2 * humidity ** 2;

        const hiCelsius = ((hi - 32) * 5) / 9;
        return Number(hiCelsius.toFixed(2));
    }

    // Wind chill (applies at low temperatures, requires wind speed)
    if (temperature <= 10 && windSpeed != null) {
        const windPower = windSpeed ** 0.16;
        const wc =
            35.74 +
            0.6215 * tempF -
            35.75 * windPower +
            0.4275 * tempF * windPower;

        const wcCelsius = ((wc - 32) * 5) / 9;
        return Number(wcCelsius.toFixed(2));
    }

    // Default: return the original temperature rounded to 2 decimals
    return Number(temperature.toFixed(2));
}
function setupCanvasDimensions() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    paddingX = 55;
    paddingY = 30;
    chartWidth = canvas.width - paddingX * 2;
    chartHeight = canvas.height - paddingY * 2;
    maxDataValue = Math.max(...temperatures);
    minDataValue = Math.min(...temperatures);
}

function getX(index) {
    return paddingX + (index * (chartWidth / (temperatures.length - 1)));
}

function getY(value) {
    const range = (maxDataValue - minDataValue) || 1;
    return canvas.height - paddingY - ((value - minDataValue) * (chartHeight / range));
}

let currentProgress = 0;
const animationSpeed = 0.015;
function easeOutCubic(x) {
    return 1 - Math.pow(1 - x, 3);
}

function animateChart() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);


    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px sans-serif';


    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';
    const labelCount = 6;
    for (let i = 0; i < labelCount; i++) {
        const ratio = i / (labelCount - 1);
        const labelValue = minDataValue + (maxDataValue - minDataValue) * ratio;
        const y = getY(labelValue);
        ctx.fillText(`${Math.round(labelValue)}°C`, paddingX - 10, y);
    }

    // X-Axis Labels (Hours)
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = '#64748b';
    hours.forEach((hour, index) => {
        ctx.fillText(hour, getX(index), canvas.height - paddingY + 10);
    });

    // --- 2. Animate Vector Line ---
    const easedProgress = easeOutCubic(currentProgress);
    const targetXMax = paddingX + (chartWidth * easedProgress);

    const lineGradient = ctx.createLinearGradient(paddingX, 0, canvas.width - paddingX, 0);
    lineGradient.addColorStop(0, '#61acf6');
    lineGradient.addColorStop(0.5, '#ffffff');
    lineGradient.addColorStop(1, '#61acf6');

    ctx.lineWidth = 5;
    ctx.strokeStyle = lineGradient;
    ctx.beginPath();
    ctx.moveTo(getX(0), getY(temperatures[0]));

    for (let i = 1; i < temperatures.length; i++) {
        const x = getX(i);
        const y = getY(temperatures[i]);
        if (x <= targetXMax) {
            ctx.lineTo(x, y);
        } else {
            const prevX = getX(i - 1);
            const prevY = getY(temperatures[i - 1]);
            const ratio = (targetXMax - prevX) / (x - prevX);
            const interpolatedY = prevY + (y - prevY) * ratio;
            ctx.lineTo(targetXMax, interpolatedY);
            break;
        }
    }
    ctx.stroke();

    // --- 3. Animation Loop Control ---
    if (currentProgress < 1) {
        currentProgress += animationSpeed;
        if (currentProgress > 1) currentProgress = 1;
        animationId = requestAnimationFrame(animateChart);
    }
}

setupCanvasDimensions();
animateChart();

window.addEventListener('resize', () => {
    if (animationId) cancelAnimationFrame(animationId); // Stop running animation
    setupCanvasDimensions();
    currentProgress = 1;
    animateChart();
});

// accessing the html tag to define content and give value
const today_temp = document.getElementById('temp-today');
today_temp.textContent = temp + '°';
const humidity_detail = document.getElementById("humidity");
humidity_detail.textContent = "Humidity " + humidity + "%";
const wind_speed_detail = document.getElementById("windspeed")
wind_speed_detail.textContent = "Wind " + windSpeed + "m/s";
const feelslike = feelsLikeTemperature(temp, humidity, windSpeed)