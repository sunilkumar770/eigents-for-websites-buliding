import Hero from '@/components/Hero'
import SearchBar from '@/components/SearchBar'
import FeaturedStores from '@/components/FeaturedStores'
import Categories from '@/components/Categories'

export default function Home() {
  return (
    <div className="bg-gradient-to-b from-blue-50 to-white">
      <Hero />
      <div className="container mx-auto px-4 py-8">
        <SearchBar />
        <Categories />
        <FeaturedStores />
      </div>
    </div>
  )
}
