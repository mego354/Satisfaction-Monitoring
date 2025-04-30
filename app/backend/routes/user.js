import express from 'express';
import bcrypt from 'bcrypt';
import { createUser, getuserBYEmail, createScore } from '../dto/user.js';


const router = express.Router();

/////////////////////////////// REGISTER ///////////////////////////////
router.post('/register'
, async (req, res) => {
    try {
        const { email, password,name } = req.body;
        const user = await getuserBYEmail(email);
        if(user) await user.deleteOne();

        const hashedPassword = await bcrypt.hash(password, 10);
        
        const createdUser = await createUser({email,password:hashedPassword,name});

        return res.status(201).json({ status:true,user_id:createdUser._id });
    } catch (error) {
        console.log(error.message)
        res.status(400).json(error.message);
    }
});

/////////////////////////////// Login ///////////////////////////////
router.post('/login'
, async (req, res) => {
    try {
        const { email, password } = req.body;
        const user = await getuserBYEmail(email);
        if(!user) return res.status(400).json({error:"Invalid email"});
        const passwordMatch = await bcrypt.compare(password, user.password);
        if (!passwordMatch) {
            return res.status(401).json({ error: 'Invalid password' });
        }
        return res.status(200).json({ status:true,user_id:user._id });
    } catch (error) {
        res.status(400).json(error.message);
    }
});

/////////////////////////////// Save score ///////////////////////////////
router.post('/score'
    , async (req, res) => {
        try {
            const { score } = req.body;
            const created_score = await createScore(score);
            return res.status(200).json({ status:true,score:created_score });
        } catch (error) {
            res.status(400).json(error.message);
        }
    });
export default router;