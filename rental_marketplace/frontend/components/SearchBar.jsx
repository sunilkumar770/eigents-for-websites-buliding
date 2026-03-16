'use client'

import { useState } from 'react'

export default function SearchBar() {
  const [query, setQuery] = useState('')
  const [location, setLocation] = useState('')

  return (
    <div className="bg-white rounded-xl shadow-lg p-6 -mt-8 relative z-10 max-w-4xl mx-auto">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <input
          type="text"
          placeholder="What do you want to rent?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="border rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="text"
          placeholder="Location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
          className="border rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500"
        />
        <button className="bg-blue-600 text-white rounded-lg px-6 py-3 font-semibold hover:bg-blue-700">
          Search
        </button>
      </div>
    </div>
  )
}
