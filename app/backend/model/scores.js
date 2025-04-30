// models/client.js
import mongoose from 'mongoose';

const scoreSchema = new mongoose.Schema({
  score: { type: String, required: true}

},{timestamps:true});

const ScoreModel = mongoose.model('scores', scoreSchema);
export default ScoreModel;
