export default function Hero() {
  return (
    <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-20">
      <div className="container mx-auto px-4 text-center">
        <h1 className="text-5xl font-bold mb-4">Rent Anything, Anywhere</h1>
        <p className="text-xl mb-8 opacity-90">
          Find cameras, bikes, equipment and more from local rental stores
        </p>
        <div className="flex justify-center gap-4">
          <a href="/stores" className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100">
            Browse Stores
          </a>
          <a href="/auth" className="border-2 border-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-blue-600">
            List Your Store
          </a>
        </div>
      </div>
    </div>
  )
}
