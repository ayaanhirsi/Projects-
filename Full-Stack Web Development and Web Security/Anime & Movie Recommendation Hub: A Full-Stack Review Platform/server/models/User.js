const mongoose = require('mongoose');
const bcrypt = require('bcryptjs'); 

const userSchema = new mongoose.Schema({
    username: { 
        type: String, 
        required: [true, 'Username is required.'], 
        unique: true, 
        trim: true,
        minlength: 3
    },
    email: { 
        type: String, 
        required: [true, 'Email is required.'], 
        unique: true, 
        lowercase: true, 
        trim: true,
        match: [/.+\@.+\..+/, 'Please enter a valid email address.']
    },
    passwordHash: { 
        type: String, 
        required: [true, 'Password is required.'] 
    },
    role: { 
        type: String, 
        enum: ['user', 'admin'], 
        default: 'user' 
    },
    createdAt: { 
        type: Date, 
        default: Date.now 
    },
});

userSchema.pre('save', async function () {
    if (this.isModified('passwordHash')) {
        this.passwordHash = await bcrypt.hash(this.passwordHash, 10);
    }
});

userSchema.methods.comparePassword = function(candidatePassword) {
    return bcrypt.compare(candidatePassword, this.passwordHash);
};

const User = mongoose.model('User', userSchema);
module.exports = User;