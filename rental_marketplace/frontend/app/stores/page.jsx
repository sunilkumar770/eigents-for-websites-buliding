import StoreList from '@/components/StoreList'
import Filters from '@/components/Filters'
import Map from '@/components/Map'

export default function StoresPage() {
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Browse Rental Stores</h1>
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Filters />
          <StoreList />
        </div>
        <div className="hidden lg:block">
          <Map />
        </div>
      </div>
    </div>
  )
}
