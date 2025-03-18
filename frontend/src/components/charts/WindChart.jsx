import { WindChart as WindChartInner } from './WeatherChart'

export default function WindChart({ data }) {
  return <WindChartInner data={data} />
}
