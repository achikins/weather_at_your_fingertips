import { TemperatureChart as TempChartInner } from './WeatherChart'

export default function TemperatureChart({ data }) {
  return <TempChartInner data={data} />
}
