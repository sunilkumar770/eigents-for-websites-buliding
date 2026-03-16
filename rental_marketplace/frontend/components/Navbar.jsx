export default function Navbar() {
  return (
    <nav className="bg-white shadow-md sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <a href="/" className="text-2xl font-bold text-blue-600">RentIt</a>
        <div className="flex gap-6">
          <a href="/stores" className="hover:text-blue-600">Browse</a>
          <a href="/dashboard" className="hover:text-blue-600">Dashboard</a>
          <a href="/auth" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
            Login
          </a>
        </div>
      </div>
    </nav>
  )
}
