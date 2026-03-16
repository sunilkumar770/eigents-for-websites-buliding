export default function StoreCard({ store }) {
  return (
    <div className="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-xl transition">
      <img src={store.image} alt={store.name} className="w-full h-48 object-cover" />
      <div className="p-4">
        <h3 className="font-bold text-lg">{store.name}</h3>
        <p className="text-gray-600 text-sm">{store.category}</p>
        <div className="flex items-center mt-2">
          <span className="text-yellow-500">★</span>
          <span className="ml-1">{store.rating}</span>
          <span className="text-gray-400 ml-2">({store.reviewCount} reviews)</span>
        </div>
        <p className="text-gray-500 text-sm mt-2">{store.location}</p>
      </div>
    </div>
  )
}
