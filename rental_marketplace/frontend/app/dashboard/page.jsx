import { getServerSession } from 'next-auth'
import Stats from '@/components/dashboard/Stats'
import Bookings from '@/components/dashboard/Bookings'
import Products from '@/components/dashboard/Products'

export default async function DashboardPage() {
  const session = await getServerSession()
  
  if (!session) {
    return <div>Please login to access dashboard</div>
  }
  
  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">Store Dashboard</h1>
      <Stats />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
        <Bookings />
        <Products />
      </div>
    </div>
  )
}
