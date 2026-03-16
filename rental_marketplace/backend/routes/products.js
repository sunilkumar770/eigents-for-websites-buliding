const express = require('express');
const db = require('../db');
const auth = require('../middleware/auth');
const router = express.Router();

// Get products by store
router.get('/store/:storeId', async (req, res) => {
  try {
    const result = await db.query(
      'SELECT * FROM products WHERE store_id = $1 AND available = true ORDER BY created_at DESC',
      [req.params.storeId]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get single product
router.get('/:id', async (req, res) => {
  try {
    const result = await db.query('SELECT * FROM products WHERE id = $1', [req.params.id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Product not found' });
    }
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create product
router.post('/', auth, async (req, res) => {
  try {
    const { store_id, name, description, price_per_day, images, category } = req.body;
    const result = await db.query(
      `INSERT INTO products (store_id, name, description, price_per_day, images, category)
       VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
      [store_id, name, description, price_per_day, images, category]
    );
    res.status(201).json(result.rows[0]);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Check availability
router.get('/:id/availability', async (req, res) => {
  try {
    const { start_date, end_date } = req.query;
    const result = await db.query(
      `SELECT * FROM bookings 
       WHERE product_id = $1 AND status = 'confirmed'
       AND NOT (end_date < $2 OR start_date > $3)`,
      [req.params.id, start_date, end_date]
    );
    res.json({ available: result.rows.length === 0 });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
