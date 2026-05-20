const Title = require('../models/Title');

exports.getAllTitles = async (req, res) => {
    try {
        const { search, type } = req.query;

        let query = {};

        if (search) {
            query.name = { $regex: search, $options: 'i' };
        }

        if (type && type !== '') {
            query.type = type;
        }

        const titles = await Title.find(query).sort({ year: -1 });

        res.status(200).json({
            success: true,
            data: titles,
            meta: { 
                total: titles.length,
                totalPages: 1 
            }
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ success: false, message: 'Server Error' });
    }
};

exports.getTitleById = async (req, res) => {
    try {
        const title = await Title.findById(req.params.id);
        if (!title) {
            return res.status(404).json({ success: false, message: 'Title not found' });
        }
        res.status(200).json({ success: true, data: title });
    } catch (error) {
        res.status(400).json({ success: false, message: 'Invalid ID' });
    }
};