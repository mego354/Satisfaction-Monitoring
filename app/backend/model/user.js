// models/client.js
import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },

},{timestamps:true});

const UserModel = mongoose.model('user', userSchema);
export default UserModel;
