const canvas = document.getElementById('myCanvasChart');
const ctx = canvas.getContext('2d');

// Example usage: (Coordinates for London)

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
};

const website_bg_color = {
    "clearsky_day": "#196db8, #78AFE9",
    "clearsky_night": "#2b32b2, #0b1021",
    "fair_day": "#6dd5fa, #2980b9",
    "partlycloudy_day": "#7abcff, #3a7bd5",
    "partlycloudy_night": "#243b55, #141e30",
    "cloudy": "#859eb1, #417a8d",
    "fog": "#9bc5c3, #4d616b",
    "lightrainshowers_day": "#78a5c3, #4b79a1",
    "rainshowers_day": "#3a6073, #5a8a9e",
    "heavyrainshowers_day": "#2f6e8c, #133843",
    "lightrain": "#344b56, #34495e",
    "rain": " #3498db ,#2c3e50",
    "heavyrain": "#1f2421, #214052",
    "lightssnowshowers_day": "#83a4d4, #b6fbff",
    "snowshowers_day": "#70a1ff, #a4b0be",
    "heavysnowshowers_day": "#57606f, #a4b0be",
    "lightsnow": "#83a4d4, #ced6e0",
    "snow": "#196db8, #78AFE9",
    "heavysnow": "#196db8, #78AFE9",
    "sleet": "#4b79a1, #283e51",
    "lightsleet": "#a7c0cd, #607d8b",
    "heavysleet": "#78909c, #37474f",
    "sleetshowers_day": "#546e7a, #90a4ae",
    "lightssleetshowers_day": "#78909c, #b0bec5",
    "heavysleetshowers_day": "#263238, #455a64",
    "thunderstorms": "#0f0c29, #24243e",
    "lightrainshowersandthunder_day": "#20002c, #cbb4d4",
    "rainandthunder": "#141e30, #421e3f",
    "heavyrainandthunder": "#000000, #434343"
};

// --- DATA INITIALIZATION ---
const jsonElement = document.getElementById('json-weather-data');
const weatherData = JSON.parse(jsonElement.textContent);
const coordinates = weatherData.geometry.coordinates;
const longitude = coordinates[0];
const latitude = coordinates[1];
const queryString = window.location.search;
const urlParams = new URLSearchParams(queryString);
const cityname = urlParams.get('cityname');
const timeseries = weatherData.properties.timeseries;

const temp = timeseries[0].data.instant.details.air_temperature;
const humidity = timeseries[0].data.instant.details.relative_humidity;
const windSpeed = timeseries[0].data.instant.details.wind_speed;

const next1 = timeseries[0]?.data?.next_1_hours ?? {};
const symbol_code = next1?.summary?.symbol_code;

const weather_discrption = document.getElementById('weather_discription');
if (weather_discrption) {
    weather_discrption.textContent = WEATHER_CONDITIONS[symbol_code] ?? "Unknown";
}

const temp24h = timeseries
    .slice(0, Math.min(24, timeseries.length))
    .map(item => item.data.instant.details.air_temperature);
const temperatures = temp24h.slice(0, 7);

// --- HELPER FUNCTIONS ---
function getNextHours(count = 7, is12Hour = true) {
    return timeseries.slice(0, count).map(entry => {
        const date = new Date(entry.time);
        return date.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
            hour12: is12Hour
        });
    });
}

function getNext10DaysName() {
    const days = [];
    const today = new Date();

    for (let i = 1; i <= 10; i++) {
        // Create a new date object for each day
        const nextDate = new Date();

        // Add i days to today's date
        nextDate.setDate(today.getDate() + i);

        // Format to get the short day name ('Mon', 'Tue', etc.)
        const dayName = nextDate.toLocaleDateString('en-US', { weekday: 'short' });

        days.push(dayName);
    }

    return days;
}
const todayKey = new Date(Date.now()).toISOString().slice(0, 10) ; 
function getNext10Days(startDateStr) {
    const [year, month, day] = startDateStr.split('-').map(Number);
    const dateKeys = [];

    for (let i = 1; i <= 10; i++) {
        const date = new Date(Date.UTC(year, month - 1, day + i));
        dateKeys.push(date.toISOString().slice(0, 10));
    }

    return dateKeys;
}

function getNext10Daysforecast(timeseries) {
    const weeklyData = {};

    for (const entry of timeseries) {
        const timeStr = entry.time;
        const dateKey = timeStr;
        const instant = entry.data?.instant?.details || {};
        const currentTemp = instant.air_temperature ?? null;

        let precip = null;
        let symbol = null;

        if ("next_1_hours" in entry.data) {
            precip = entry.data.next_1_hours.details?.precipitation_amount ?? null;
            symbol = entry.data.next_1_hours.summary?.symbol_code ?? null;
        } else if ("next_6_hours" in entry.data) {
            precip = entry.data.next_6_hours.details?.precipitation_amount ?? null;
            symbol = entry.data.next_6_hours.summary?.symbol_code ?? null;
        }

        const record = {
            time: timeStr,
            temp: currentTemp,
            wind_speed: instant.wind_speed ?? null,
            pressure: instant.air_pressure_at_sea_level ?? null,
            precip: precip,
            symbol: symbol,
        };

        if (!weeklyData[dateKey]) {
            weeklyData[dateKey] = { entries: [], min_temp: null, max_temp: null };
        }

        weeklyData[dateKey].entries.push(record);

        if (currentTemp !== null) {
            if (weeklyData[dateKey].min_temp === null || currentTemp < weeklyData[dateKey].min_temp) {
                weeklyData[dateKey].min_temp = currentTemp;
            }
            if (weeklyData[dateKey].max_temp === null || currentTemp > weeklyData[dateKey].max_temp) {
                weeklyData[dateKey].max_temp = currentTemp;
            }
        }
    }

    const weekly = {};
    const keys = Object.keys(weeklyData);

    for (let i = 0; i < keys.length; i++) {
        const dayKey = keys[i].substring(0, 10);
        if (!(dayKey in weekly)) {
            weekly[i] = weeklyData[keys[i]];
        }
    }

    return weekly;
}

function getTenDayForecast(timeseries) {
    const weeklyData = processWeatherData(timeseries);
    const forecastDays = Object.keys(weeklyData).slice(0, 10);

    return forecastDays.map((day) => {
        const data = weeklyData[day];
        const entries = data.entries;
        const middayEntry = entries.find(e => e.time.includes("T12:00:00Z")) || entries[0];

        return {
            date: day,
            min_temp: data.min_temp,
            max_temp: data.max_temp,
            symbol: middayEntry?.symbol ?? null,
            weather_code: middayEntry?.symbol ?? null,
            total_entries: entries.length
        };
    });
}

function feelsLikeTemperature(temperature, humidity, windSpeed) {
    if (temperature == null) return null;
    const tempF = (temperature * 9) / 5 + 32;

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

        return Number((((hi - 32) * 5) / 9).toFixed(2));
    }

    if (temperature <= 10 && windSpeed != null) {
        const windPower = windSpeed ** 0.16;
        const wc =
            35.74 +
            0.6215 * tempF -
            35.75 * windPower +
            0.4275 * tempF * windPower;

        return Number((((wc - 32) * 5) / 9).toFixed(2));
    }

    return Number(temperature.toFixed(2));
}

// --- CANVAS METRICS & RENDER ---
const hours = getNextHours(7, true);
let chartWidth, chartHeight, paddingX, paddingY, maxDataValue, minDataValue;
let animationId = null;

function setupCanvasDimensions() {
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width;
    canvas.height = rect.height;
    paddingX = 45;
    paddingY = 35;
    chartWidth = canvas.width - paddingX * 2;
    chartHeight = canvas.height - paddingY * 2;

    // Add margin to min/max so chart lines don't hit hard edges
    const maxVal = Math.max(...temperatures);
    const minVal = Math.min(...temperatures);
    const margin = Math.max((maxVal - minVal) * 0.2, 1);

    maxDataValue = maxVal + margin;
    minDataValue = minVal - margin;
}

function getX(index) {
    return paddingX + (index * (chartWidth / (temperatures.length - 1)));
}

function getY(value) {
    const range = (maxDataValue - minDataValue) || 1;
    return canvas.height - paddingY - ((value - minDataValue) * (chartHeight / range));
}

let currentProgress = 0;
const animationSpeed = 0.02;

function easeOutCubic(x) {
    return 1 - Math.pow(1 - x, 3);
}

function animateChart() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. Draw Axis & Labels
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';
    ctx.textBaseline = 'middle';

    const labelCount = 5;
    for (let i = 0; i < labelCount; i++) {
        const ratio = i / (labelCount - 1);
        const labelValue = minDataValue + (maxDataValue - minDataValue) * ratio;
        const y = getY(labelValue);
        ctx.fillText(`${Math.round(labelValue)}°`, paddingX - 10, y);
    }

    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = '#64748b';
    hours.forEach((hour, index) => {
        ctx.fillText(hour, getX(index), canvas.height - paddingY + 12);
    });

    // 2. Animate Vector Line
    const easedProgress = easeOutCubic(currentProgress);
    const targetXMax = paddingX + (chartWidth * easedProgress);

    const lineGradient = ctx.createLinearGradient(paddingX, 0, canvas.width - paddingX, 0);
    lineGradient.addColorStop(0, '#61acf6');
    lineGradient.addColorStop(0.5, '#ffffff');
    lineGradient.addColorStop(1, '#61acf6');

    ctx.lineWidth = 4;
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

    // 3. Draw Points & Values
    for (let i = 0; i < temperatures.length; i++) {
        const x = getX(i);
        if (x <= targetXMax) {
            const y = getY(temperatures[i]);
            ctx.fillStyle = '#ffffff';
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();

            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 11px sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(`${Math.round(temperatures[i])}°`, x, y - 16);
        }
    }

    // 4. Loop Frame
    if (currentProgress < 1) {
        currentProgress += animationSpeed;
        if (currentProgress > 1) currentProgress = 1;
        animationId = requestAnimationFrame(animateChart);
    }
}

// Initialization & Events
setupCanvasDimensions();
animateChart();

window.addEventListener('resize', () => {
    if (animationId) cancelAnimationFrame(animationId);
    setupCanvasDimensions();
    currentProgress = 1;
    animateChart();
});

// UI Dynamic Updates
const getNext10Dayskey = getNext10Days(todayKey);
const weekly_forecast = getNext10Daysforecast(timeseries);
const dayname = getNext10DaysName();
const bg_color = website_bg_color[symbol_code] ?? website_bg_color["clearsky_day"];
document.body.style.backgroundImage = `radial-gradient(${bg_color})`;
const location_tab = document.getElementById("location-name");
location_tab.textContent = cityname;
const today_temp = document.getElementById('temp-today');
if (today_temp) today_temp.textContent = `${temp}°`;

const humidity_detail = document.getElementById("humidity");
if (humidity_detail) humidity_detail.textContent = `Humidity ${humidity}%`;

const wind_speed_detail = document.getElementById("windspeed");
if (wind_speed_detail) wind_speed_detail.textContent = `Wind ${windSpeed}m/s`;

const feelsliketemp = feelsLikeTemperature(temp, humidity, windSpeed);
const feelslike_doc = document.getElementById("feels-like")
feelslike_doc.textContent = `${feelsliketemp}°`;

const day1name = document.getElementById("day1name");
day1name.textContent = dayname[0];
const day2name = document.getElementById("day2name");
day2name.textContent = dayname[1];
const day3name = document.getElementById("day3name");
day3name.textContent = dayname[2];
const day4name = document.getElementById("day4name");
day4name.textContent = dayname[3];
const day5name = document.getElementById("day5name");
day5name.textContent = dayname[4];
const day6name = document.getElementById("day6name");
day6name.textContent = dayname[5];
const day7name = document.getElementById("day7name");
day7name.textContent = dayname[6];
const day8name = document.getElementById("day8name");
day8name.textContent = dayname[7];
const day9name = document.getElementById("day9name");
day9name.textContent = dayname[8];
const day10name = document.getElementById("day10name");
day10name.textContent = dayname[9];
const day1temp = document.getElementById("day1temp");
// day1temp.innerHTML = `${weekly_forecast.${}}.°<span>${}°</span>`;
const day2temp = document.getElementById("day2temp");
// day1temp.innerHTML = `${weekly_forecast.}°<span>${}°</span>`;
const day3temp = document.getElementById("day3temp");
// day1temp.innerHTML = `${weekly_forecast.}°<span>${}°</span>`;
const day4temp = document.getElementById("day4temp");
// day1temp.innerHTML = `${weekly_forecast.}°<span>${}°</span>`;
const day5temp = document.getElementById("day5temp");
// day1temp.innerHTML = `${weekly_forecast.}°<span>${}°</span>`;
const day6temp = document.getElementById("day6temp");
// day1temp.innerHTML = `${weekly_forecast.}°<span>${}°</span>`;
const day7temp = document.getElementById("day7temp");
// day1temp.innerHTML = `${weekly_forecast.}°<span>${}°</span>`;
const day8temp = document.getElementById("day8temp");
// day1temp.innerHTML = `${weekly_forecast.}°<span>${}°</span>`;
const day9temp = document.getElementById("day9temp");
// day1temp.innerHTML = `${weekly_forecast.}°<span>${}°</span>`;
const day10temp = document.getElementById("day10temp");
