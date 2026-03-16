const express = require('express');
const db = require('../db');
const auth = require('../middleware/auth');
const router = express.Router();

// Get store reviews
router.get('/store/:storeId', async (req, res) => {
  try {
    const result = await db.query(
      `SELECT r.*, u.name as user_name
       FROM reviews r
       JOIN users u ON r.user_id = u.id
       WHERE r.store_id = $1
       ORDER BY r.created_at DESC`,
      [req.params.storeId]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create review
router.post('/', auth, async (req, res) => {
  try {
    const { store_id, booking_id, rating, comment } = req.body;
    
    const result = await db.query(
      `INSERT INTO reviews (user_id, store_id, booking_id, rating, comment)
       VALUES ($1, $2, $3, $4, $5) RETURNING *`,
      [req.userId, store_id, booking_id, rating, comment]
    );
    
    // Update store rating
    await db.query(
      `UPDATE stores SET rating = (SELECT AVG(rating) FROM reviews WHERE store_id = $1)
       WHERE id = $1`,
      [store_id]
    );
    
    res.status(201).json(result.rows[0]);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

module.exports = router;
