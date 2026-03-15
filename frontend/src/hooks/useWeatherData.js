import { useState, useCallback } from 'react'
import { mockWeatherData, weatherAlerts, getWeatherForCity, getAlertsForCity } from '../data/mockWeatherData'
import { australianCities, getCityById } from '../data/australianCities'

export const useWeatherData = () => {
  const [selectedCity, setSelectedCity] = useState(australianCities[0]) // Sydney default
  const [compareCity1, setCompareCity1] = useState(australianCities[0])
  const [compareCity2, setCompareCity2] = useState(australianCities[1])
  const [activeLayer, setActiveLayer] = useState('temperature')

  const selectCity = useCallback((cityId) => {
    const city = getCityById(cityId)
    if (city) setSelectedCity(city)
  }, [])

  const setCompareCity = useCallback((slot, cityId) => {
    const city = getCityById(cityId)
    if (!city) return
    if (slot === 1) setCompareCity1(city)
    else setCompareCity2(city)
  }, [])

  const getMonthlyData = useCallback(
    (cityId) => {
      const id = cityId || selectedCity?.id
      return getWeatherForCity(id)?.monthly || []
    },
    [selectedCity]
  )

  const getCurrentConditions = useCallback(
    (cityId) => {
      const id = cityId || selectedCity?.id
      return getWeatherForCity(id)?.current || null
    },
    [selectedCity]
  )

  const getAlerts = useCallback(
    (cityId) => {
      if (cityId) return getAlertsForCity(cityId)
      return weatherAlerts
    },
    []
  )

  const getLayerData = useCallback(
    (cityId) => {
      const id = cityId || selectedCity?.id
      const monthly = getWeatherForCity(id)?.monthly || []
      const current = getWeatherForCity(id)?.current || {}
      return { monthly, current }
    },
    [selectedCity]
  )

  return {
    cities: australianCities,
    selectedCity,
    compareCity1,
    compareCity2,
    activeLayer,
    setActiveLayer,
    selectCity,
    setCompareCity,
    getMonthlyData,
    getCurrentConditions,
    getAlerts,
    getLayerData,
    allWeatherData: mockWeatherData,
  }
}
