import AlertsPanel from '../components/alerts/AlertsPanel'
import AlertBanner from '../components/alerts/AlertBanner'

export default function AlertsPage() {
  return (
    <div className="h-full overflow-y-auto px-4 lg:px-6 py-5 animate-fade-in">
      <div className="mb-4">
        <AlertBanner />
      </div>
      <AlertsPanel />
    </div>
  )
}
