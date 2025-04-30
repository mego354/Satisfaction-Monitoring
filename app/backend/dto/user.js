import UserModel from "../model/user.js";
import ScoreModel from "../model/scores.js";

export const getuserBYEmail = async(email) =>{
    return await UserModel.findOne({email});
}

export const createUser = async(data)=>{
    try{
        const user = new UserModel(data);
        await user.save();
        return user;
    }
    catch(error){
        console.log(error)
        throw new Error("Can not create this user");
    }   
}

export const getuserByID = async(user_id) =>{
    return await UserModel.findById(user_id);
}


export const createScore = async(score)=>{
    try{
        const created_score = new ScoreModel({score:score});
        await created_score.save();
        return created_score;
    }
    catch(error){
        console.log(error)
        throw new Error("Can not create this score");
    }   
}