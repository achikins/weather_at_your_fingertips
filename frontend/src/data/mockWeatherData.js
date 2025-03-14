const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// Each city has 12 months of: tempMin, tempMax, tempAvg (°C), rainfall (mm), humidity (%), windSpeed (km/h)
const rawData = {
  sydney: {
    tempMin:    [18, 18, 16, 13, 10,  8,  7,  8, 10, 13, 15, 17],
    tempMax:    [26, 26, 24, 22, 19, 16, 16, 17, 20, 22, 24, 25],
    tempAvg:    [22, 22, 20, 17, 14, 12, 11, 12, 15, 17, 19, 21],
    rainfall:   [103, 117, 131, 126, 120,  132, 97, 81, 68, 76, 83, 77],
    humidity:   [65, 67, 68, 69, 70, 70, 67, 63, 62, 61, 62, 63],
    windSpeed:  [19, 18, 17, 18, 19, 19, 21, 21, 22, 22, 21, 20],
  },
  melbourne: {
    tempMin:    [14, 14, 12,  9,  7,  5,  4,  5,  7,  9, 11, 13],
    tempMax:    [26, 26, 24, 20, 17, 14, 13, 15, 17, 20, 22, 24],
    tempAvg:    [20, 20, 18, 14, 12,  9,  8, 10, 12, 14, 17, 19],
    rainfall:   [48, 47, 52, 57, 57, 49, 48, 49, 58, 66, 59, 59],
    humidity:   [57, 58, 60, 65, 71, 75, 75, 70, 65, 60, 57, 56],
    windSpeed:  [21, 20, 20, 21, 21, 21, 22, 22, 24, 24, 23, 22],
  },
  brisbane: {
    tempMin:    [21, 21, 19, 16, 13, 10,  9, 10, 13, 17, 19, 20],
    tempMax:    [29, 29, 28, 26, 23, 21, 20, 22, 25, 27, 28, 29],
    tempAvg:    [25, 25, 23, 21, 18, 15, 14, 16, 19, 22, 23, 24],
    rainfall:   [159, 158, 141, 93, 73, 67, 56, 46, 46, 75, 97, 133],
    humidity:   [71, 72, 69, 66, 63, 60, 57, 54, 55, 59, 64, 69],
    windSpeed:  [15, 14, 14, 14, 15, 15, 16, 17, 17, 17, 16, 15],
  },
  perth: {
    tempMin:    [17, 18, 16, 13, 10,  8,  7,  7,  9, 11, 13, 16],
    tempMax:    [31, 32, 29, 25, 21, 18, 17, 18, 20, 23, 26, 29],
    tempAvg:    [24, 25, 22, 19, 15, 13, 12, 12, 14, 17, 20, 22],
    rainfall:   [10,  9, 18, 43, 116, 181, 172, 134, 79, 56, 21, 12],
    humidity:   [43, 44, 47, 54, 63, 70, 70, 66, 59, 52, 44, 42],
    windSpeed:  [22, 21, 21, 20, 19, 19, 20, 21, 22, 24, 24, 23],
  },
  adelaide: {
    tempMin:    [16, 16, 14, 11,  9,  7,  6,  7,  9, 11, 13, 15],
    tempMax:    [29, 29, 26, 22, 18, 15, 15, 16, 18, 22, 25, 27],
    tempAvg:    [22, 22, 20, 17, 13, 11, 10, 11, 13, 16, 19, 21],
    rainfall:   [20, 15, 26, 43, 58, 78, 67, 57, 43, 41, 29, 30],
    humidity:   [40, 41, 44, 51, 61, 68, 68, 62, 56, 49, 43, 40],
    windSpeed:  [21, 20, 19, 19, 19, 19, 20, 20, 21, 22, 21, 21],
  },
  darwin: {
    tempMin:    [25, 25, 24, 23, 20, 18, 17, 19, 23, 25, 26, 26],
    tempMax:    [32, 31, 32, 33, 33, 31, 31, 32, 33, 34, 34, 33],
    tempAvg:    [29, 28, 28, 28, 26, 24, 24, 25, 28, 29, 30, 29],
    rainfall:   [386, 315, 254, 97, 15,  1,  1,  3,  13, 70, 145, 243],
    humidity:   [75, 77, 74, 62, 47, 38, 34, 36, 43, 55, 66, 73],
    windSpeed:  [14, 14, 15, 14, 17, 20, 21, 21, 22, 21, 17, 15],
  },
  hobart: {
    tempMin:    [11, 12, 10,  8,  6,  4,  3,  4,  6,  7,  9, 10],
    tempMax:    [22, 22, 20, 17, 14, 12, 11, 12, 15, 17, 19, 21],
    tempAvg:    [17, 17, 15, 12, 10,  8,  7,  8, 10, 12, 14, 16],
    rainfall:   [47, 40, 44, 53, 47, 57, 53, 52, 52, 63, 55, 57],
    humidity:   [57, 58, 60, 65, 70, 73, 73, 69, 65, 61, 58, 56],
    windSpeed:  [18, 17, 17, 17, 18, 18, 18, 19, 20, 20, 19, 19],
  },
  cairns: {
    tempMin:    [24, 24, 23, 22, 19, 17, 16, 17, 19, 22, 23, 24],
    tempMax:    [32, 31, 31, 29, 27, 25, 25, 26, 28, 30, 31, 32],
    tempAvg:    [28, 27, 27, 25, 23, 21, 20, 21, 23, 26, 27, 28],
    rainfall:   [392, 428, 426, 195, 92, 47, 28, 27, 35, 35, 90, 176],
    humidity:   [76, 78, 77, 74, 69, 65, 61, 59, 60, 63, 68, 73],
    windSpeed:  [13, 12, 12, 11, 11, 11, 12, 13, 14, 14, 13, 13],
  },
  goldcoast: {
    tempMin:    [21, 21, 19, 17, 13, 11, 10, 11, 14, 17, 19, 21],
    tempMax:    [29, 29, 27, 25, 22, 20, 19, 21, 24, 26, 27, 29],
    tempAvg:    [25, 25, 23, 21, 17, 15, 14, 16, 19, 21, 23, 25],
    rainfall:   [168, 167, 153, 103, 85, 80, 57, 55, 55, 89, 107, 148],
    humidity:   [72, 73, 71, 68, 64, 61, 57, 56, 58, 62, 67, 71],
    windSpeed:  [14, 13, 13, 14, 14, 14, 15, 16, 17, 17, 15, 14],
  },
  canberra: {
    tempMin:    [13, 13, 10,  6,  2,  0, -1,  0,  4,  7, 10, 12],
    tempMax:    [28, 27, 24, 20, 14, 11, 10, 12, 16, 20, 23, 27],
    tempAvg:    [20, 20, 17, 13,  8,  5,  4,  6, 10, 13, 16, 19],
    rainfall:   [57, 55, 51, 45, 45, 38, 39, 42, 48, 55, 58, 49],
    humidity:   [52, 54, 56, 59, 66, 71, 68, 61, 55, 50, 49, 50],
    windSpeed:  [16, 15, 14, 13, 13, 12, 13, 14, 15, 16, 16, 16],
  },
}

// Build the full monthly dataset for a city
const buildMonthlyData = (cityId) => {
  const d = rawData[cityId]
  return MONTHS.map((month, i) => ({
    month,
    monthIndex: i,
    tempMin: d.tempMin[i],
    tempMax: d.tempMax[i],
    tempAvg: d.tempAvg[i],
    rainfall: d.rainfall[i],
    humidity: d.humidity[i],
    windSpeed: d.windSpeed[i],
  }))
}

// Current conditions (snapshot for the map popup / weather cards)
const currentConditions = {
  sydney:    { temp: 23, condition: 'Partly Cloudy', humidity: 65, windSpeed: 19, rainfall: 4.2, uvIndex: 7 },
  melbourne: { temp: 17, condition: 'Cloudy',        humidity: 72, windSpeed: 22, rainfall: 1.1, uvIndex: 4 },
  brisbane:  { temp: 27, condition: 'Sunny',         humidity: 60, windSpeed: 14, rainfall: 0.0, uvIndex: 9 },
  perth:     { temp: 28, condition: 'Clear',         humidity: 38, windSpeed: 24, rainfall: 0.0, uvIndex: 10 },
  adelaide:  { temp: 22, condition: 'Sunny',         humidity: 42, windSpeed: 18, rainfall: 0.0, uvIndex: 8 },
  darwin:    { temp: 30, condition: 'Humid & Hazy',  humidity: 78, windSpeed: 14, rainfall: 12.5, uvIndex: 11 },
  hobart:    { temp: 14, condition: 'Showers',       humidity: 70, windSpeed: 19, rainfall: 3.8, uvIndex: 3 },
  cairns:    { temp: 29, condition: 'Tropical Storm',humidity: 80, windSpeed: 13, rainfall: 28.0, uvIndex: 6 },
  goldcoast: { temp: 26, condition: 'Sunny',         humidity: 66, windSpeed: 15, rainfall: 0.0, uvIndex: 8 },
  canberra:  { temp: 18, condition: 'Clear',         humidity: 48, windSpeed: 13, rainfall: 0.0, uvIndex: 7 },
}

// Aggregate monthly data for all cities
export const mockWeatherData = Object.keys(rawData).reduce((acc, cityId) => {
  acc[cityId] = {
    monthly: buildMonthlyData(cityId),
    current: currentConditions[cityId],
  }
  return acc
}, {})

// Extreme weather alerts
export const weatherAlerts = [
  {
    id: 'alert-1',
    cityId: 'cairns',
    cityName: 'Cairns',
    type: 'Severe Storm',
    severity: 'extreme',
    title: 'Tropical Cyclone Warning',
    description: 'A category 3 tropical cyclone is expected to make landfall within 48 hours. Residents should prepare emergency kits and follow evacuation orders.',
    issued: '2026-03-14T06:00:00Z',
    expires: '2026-03-17T18:00:00Z',
    affectedAreas: ['Cairns CBD', 'Northern Beaches', 'Port Douglas', 'Innisfail'],
  },
  {
    id: 'alert-2',
    cityId: 'darwin',
    cityName: 'Darwin',
    type: 'Heavy Rainfall',
    severity: 'high',
    title: 'Flash Flood Watch',
    description: 'Heavy monsoon rainfall expected. Low-lying areas and creek crossings may flood rapidly. Do not attempt to cross flooded roads.',
    issued: '2026-03-15T00:00:00Z',
    expires: '2026-03-16T12:00:00Z',
    affectedAreas: ['Darwin CBD', 'Palmerston', 'Litchfield', 'Howard Springs'],
  },
  {
    id: 'alert-3',
    cityId: 'perth',
    cityName: 'Perth',
    type: 'Heatwave',
    severity: 'high',
    title: 'Extreme Heat Advisory',
    description: 'Temperatures forecast to exceed 40°C over the next 3 days. Stay hydrated, avoid outdoor activities during peak heat (11am–4pm), and check on vulnerable neighbours.',
    issued: '2026-03-13T09:00:00Z',
    expires: '2026-03-18T20:00:00Z',
    affectedAreas: ['Perth Metropolitan Area', 'Swan Valley', 'Hills District'],
  },
  {
    id: 'alert-4',
    cityId: 'hobart',
    cityName: 'Hobart',
    type: 'Strong Winds',
    severity: 'moderate',
    title: 'Wind Warning — Gales Expected',
    description: 'South-westerly gales of 80–100 km/h expected over highland areas. Secure loose outdoor items and be cautious when driving high-sided vehicles.',
    issued: '2026-03-15T03:00:00Z',
    expires: '2026-03-16T06:00:00Z',
    affectedAreas: ['Central Highlands', 'Derwent Valley', 'Mount Wellington'],
  },
  {
    id: 'alert-5',
    cityId: 'sydney',
    cityName: 'Sydney',
    type: 'Coastal Hazard',
    severity: 'moderate',
    title: 'Hazardous Surf Warning',
    description: 'Swells of 3–4 metres expected along open ocean beaches. Swimming and surfing are dangerous. Only experienced surfers in appropriate locations.',
    issued: '2026-03-15T05:00:00Z',
    expires: '2026-03-16T18:00:00Z',
    affectedAreas: ['Northern Beaches', 'Eastern Suburbs', 'Illawarra Coast'],
  },
  {
    id: 'alert-6',
    cityId: 'melbourne',
    cityName: 'Melbourne',
    type: 'Thunderstorm',
    severity: 'low',
    title: 'Thunderstorm Outlook',
    description: 'Isolated severe thunderstorms possible this afternoon with large hail and damaging winds. Monitor forecasts and seek shelter if storms develop.',
    issued: '2026-03-15T07:00:00Z',
    expires: '2026-03-15T22:00:00Z',
    affectedAreas: ['CBD', 'Eastern Suburbs', 'Dandenong Ranges'],
  },
]

export const getWeatherForCity = (cityId) => mockWeatherData[cityId] || null
export const getAlertsForCity = (cityId) => weatherAlerts.filter((a) => a.cityId === cityId)
export const getAllAlerts = () => weatherAlerts
