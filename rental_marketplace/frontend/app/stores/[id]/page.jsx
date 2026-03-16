import StoreInfo from '@/components/StoreInfo'
import ProductList from '@/components/ProductList'
import Reviews from '@/components/Reviews'

export default function StoreDetailPage({ params }) {
  return (
    <div className="container mx-auto px-4 py-8">
      <StoreInfo storeId={params.id} />
      <ProductList storeId={params.id} />
      <Reviews storeId={params.id} />
    </div>
  )
}
