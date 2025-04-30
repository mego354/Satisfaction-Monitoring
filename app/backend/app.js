import express from 'express';
import dotenv from 'dotenv';
import mongoose from 'mongoose';
import Routes from "./routes/user.js";
import cors from "cors";

// Load environment variables from .env file
dotenv.config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware to parse JSON
app.use(express.json());
const corsOptions = {
    origin: 'http://localhost:3000', // Allow only this origin
    methods: 'GET,HEAD,PUT,PATCH,POST,DELETE',
    optionsSuccessStatus: 204,
  };
  
  app.use(cors(corsOptions));

app.use("",Routes);
// MongoDB Init
mongoose.connect(process.env.MONGO_URI, {}).then(() => {
    console.log('Connected to MongoDB');
}).catch(err => console.error('Error connecting to MongoDB:', err));

export const db = mongoose.connection;

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
