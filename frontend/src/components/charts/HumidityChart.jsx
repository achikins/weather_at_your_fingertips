import { HumidityChart as HumidityChartInner } from './WeatherChart'

export default function HumidityChart({ data }) {
  return <HumidityChartInner data={data} />
}
