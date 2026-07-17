const canvas = document.getElementById('myCanvasChart');
const ctx = canvas.getContext('2d');

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
const jsonElement = document.getElementById('json-weather-data');
const weatherData = JSON.parse(jsonElement.textContent);

const timeseries = weatherData.properties.timeseries;
const temp = timeseries[0].data.instant.details.air_temperature;
const textElement = document.getElementById('temp-today');
const temp24h = timeseries
    .slice(0, Math.min(24, timeseries.length))
    .map(item => item.data.instant.details.air_temperature);
textElement.textContent = (temp);
const next1 = timeseries[0]?.data?.next_1_hours ?? {};
const symbol_code = next1?.summary?.symbol_code;
const weather_discrption = document.getElementById('weather_discription');
weather_discrption.textContent = this.WEATHER_CONDITIONS[symbol_code] ?? "Unknown" ;
const temperatures = temp24h.slice(0, 5);
const hours = ['8 AM', '10 AM', '12 PM', '2 PM', '4 PM', '6 PM', '8 PM'];

let chartWidth, chartHeight, paddingX, paddingY, maxDataValue, minDataValue;

function setupCanvasDimensions() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    paddingX = 55;
    paddingY = 25;
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
const animationSpeed = 0.005;

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

    const lineGradient = ctx.createLinearGradient(paddingX, 0, canvas.width - paddingX, 0);
    lineGradient.addColorStop(0, '#61acf6');
    lineGradient.addColorStop(0.5, '#2f7dc2');
    lineGradient.addColorStop(1, '#61acf6');

    ctx.lineWidth = 5;
    ctx.strokeStyle = lineGradient;
    ctx.beginPath();
    ctx.moveTo(getX(0), getY(temperatures[0]));

    const targetXMax = paddingX + (chartWidth * currentProgress);

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

    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';

    temperatures.forEach((value, index) => {
        const x = getX(index);
        const y = getY(value);
        if (x <= targetXMax) {
            ctx.fillStyle = '#64748b';
            ctx.fillText(hours[index], x, canvas.height - paddingY + 8);
        }
    });

    if (currentProgress < 1) {
        currentProgress += animationSpeed;
        if (currentProgress > 1) currentProgress = 1;
        requestAnimationFrame(animateChart);
    }
}

setupCanvasDimensions();
animateChart();

window.addEventListener('resize', () => {
    setupCanvasDimensions();
    currentProgress = 1;
    animateChart();
});