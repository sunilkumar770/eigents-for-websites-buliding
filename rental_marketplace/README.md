# RentIt - Rental Marketplace

A peer-to-peer rental marketplace built with Next.js and Node.js.

## Quick Start

### Development

1. **Install dependencies:**
```bash
# Frontend
cd frontend && npm install

# Backend
cd backend && npm install
```

2. **Set up database:**
```bash
# Start PostgreSQL
docker-compose up db -d

# Run migrations
cd backend && npm run migrate
```

3. **Configure environment:**
```bash
# Copy environment files
cp backend/.env.example backend/.env
# Edit with your keys
```

4. **Start development servers:**
```bash
# Terminal 1 - Backend
cd backend && npm run dev

# Terminal 2 - Frontend
cd frontend && npm run dev
```

5. **Open browser:** http://localhost:3000

### Production (Docker)

```bash
docker-compose up --build
```

## Features

- ✅ Multi-vendor rental stores
- ✅ Product listings with photos
- ✅ Calendar-based booking
- ✅ Stripe payment processing
- ✅ Reviews & ratings
- ✅ Google Maps integration
- ✅ User authentication
- ✅ Store dashboard

## Tech Stack

- **Frontend:** Next.js 14, React, TailwindCSS
- **Backend:** Node.js, Express
- **Database:** PostgreSQL
- **Payments:** Stripe
- **Auth:** NextAuth.js + JWT
- **Maps:** Google Maps API

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register user |
| POST | /api/auth/login | Login |
| GET | /api/stores | List stores |
| GET | /api/stores/:id | Store detail |
| POST | /api/stores | Create store |
| GET | /api/products/store/:id | Store products |
| POST | /api/bookings | Create booking |
| POST | /api/payments/create-intent | Payment |

## License

MIT
