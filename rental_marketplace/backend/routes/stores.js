const express = require('express');
const db = require('../db');
const auth = require('../middleware/auth');
const router = express.Router();

// Get all stores
router.get('/', async (req, res) => {
  try {
    const { category, location, search } = req.query;
    let query = 'SELECT * FROM stores WHERE verified = true';
    const params = [];
    
    if (category) {
      params.push(category);
      query += ` AND category = $${params.length}`;
    }
    if (search) {
      params.push(`%${search}%`);
      query += ` AND name ILIKE $${params.length}`;
    }
    
    const result = await db.query(query + ' ORDER BY rating DESC', params);
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Get single store
router.get('/:id', async (req, res) => {
  try {
    const result = await db.query('SELECT * FROM stores WHERE id = $1', [req.params.id]);
    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'Store not found' });
    }
    res.json(result.rows[0]);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Create store (owner only)
router.post('/', auth, async (req, res) => {
  try {
    const { name, description, category, address, lat, lng } = req.body;
    const result = await db.query(
      `INSERT INTO stores (owner_id, name, description, category, address, lat, lng)
       VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *`,
      [req.userId, name, description, category, address, lat, lng]
    );
    res.status(201).json(result.rows[0]);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Update store
router.put('/:id', auth, async (req, res) => {
  try {
    const { name, description, category, address } = req.body;
    const result = await db.query(
      `UPDATE stores SET name = $1, description = $2, category = $3, address = $4, updated_at = NOW()
       WHERE id = $5 AND owner_id = $6 RETURNING *`,
      [name, description, category, address, req.params.id, req.userId]
    );
    res.json(result.rows[0]);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

module.exports = router;
