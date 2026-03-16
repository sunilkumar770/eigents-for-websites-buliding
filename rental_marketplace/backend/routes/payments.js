const express = require('express');
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const db = require('../db');
const auth = require('../middleware/auth');
const router = express.Router();

// Create payment intent
router.post('/create-intent', auth, async (req, res) => {
  try {
    const { booking_id, amount } = req.body;
    
    const paymentIntent = await stripe.paymentIntents.create({
      amount: Math.round(amount * 100),
      currency: 'usd',
      metadata: { booking_id, user_id: req.userId }
    });
    
    res.json({ clientSecret: paymentIntent.client_secret });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Confirm payment
router.post('/confirm', auth, async (req, res) => {
  try {
    const { booking_id, payment_intent_id } = req.body;
    
    // Update booking status
    await db.query(
      `UPDATE bookings SET status = 'confirmed', payment_id = $1 WHERE id = $2`,
      [payment_intent_id, booking_id]
    );
    
    res.json({ success: true });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Request refund
router.post('/refund', auth, async (req, res) => {
  try {
    const { booking_id } = req.body;
    
    const booking = await db.query('SELECT * FROM bookings WHERE id = $1', [booking_id]);
    if (booking.rows.length === 0) {
      return res.status(404).json({ error: 'Booking not found' });
    }
    
    const refund = await stripe.refunds.create({
      payment_intent: booking.rows[0].payment_id
    });
    
    await db.query(
      `UPDATE bookings SET status = 'refunded' WHERE id = $1`,
      [booking_id]
    );
    
    res.json({ refund });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

module.exports = router;
