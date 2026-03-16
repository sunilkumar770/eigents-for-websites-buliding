const express = require('express');
const db = require('../db');
const auth = require('../middleware/auth');
const router = express.Router();

// Get user bookings
router.get('/my', auth, async (req, res) => {
  try {
    const result = await db.query(
      `SELECT b.*, p.name as product_name, s.name as store_name
       FROM bookings b
       JOIN products p ON b.product_id = p.id
       JOIN stores s ON p.store_id = s.id
       WHERE b.user_id = $1
       ORDER BY b.created_at DESC`,
      [req.userId]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get store bookings (for owners)
router.get('/store/:storeId', auth, async (req, res) => {
  try {
    const result = await db.query(
      `SELECT b.*, p.name as product_name, u.name as customer_name
       FROM bookings b
       JOIN products p ON b.product_id = p.id
       JOIN users u ON b.user_id = u.id
       WHERE p.store_id = $1
       ORDER BY b.start_date ASC`,
      [req.params.storeId]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create booking
router.post('/', auth, async (req, res) => {
  try {
    const { product_id, start_date, end_date, total_amount } = req.body;
    
    // Check availability
    const available = await db.query(
      `SELECT * FROM bookings 
       WHERE product_id = $1 AND status = 'confirmed'
       AND NOT (end_date < $2 OR start_date > $3)`,
      [product_id, start_date, end_date]
    );
    
    if (available.rows.length > 0) {
      return res.status(400).json({ error: 'Product not available for selected dates' });
    }
    
    const result = await db.query(
      `INSERT INTO bookings (user_id, product_id, start_date, end_date, total_amount, status)
       VALUES ($1, $2, $3, $4, $5, 'pending') RETURNING *`,
      [req.userId, product_id, start_date, end_date, total_amount]
    );
    res.status(201).json(result.rows[0]);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Update booking status
router.patch('/:id/status', auth, async (req, res) => {
  try {
    const { status } = req.body;
    const result = await db.query(
      'UPDATE bookings SET status = $1, updated_at = NOW() WHERE id = $2 RETURNING *',
      [status, req.params.id]
    );
    res.json(result.rows[0]);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

module.exports = router;
