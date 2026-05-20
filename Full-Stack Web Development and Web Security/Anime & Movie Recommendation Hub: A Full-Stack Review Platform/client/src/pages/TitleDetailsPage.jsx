import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import api from '../services/api';
import { useAuth } from '../context/AuthContext.jsx'; 

const TitleDetailsPage = () => {
    const { id } = useParams();
    const { isAuthenticated } = useAuth();
    
    const [title, setTitle] = useState(null);
    const [reviews, setReviews] = useState([]);
    const [rating, setRating] = useState(10);
    const [reviewText, setReviewText] = useState('');

    const fetchData = useCallback(async () => {
        try {
            const tRes = await api.get(`/titles/${id}`);
            setTitle(tRes.data.data);
            const rRes = await api.get(`/reviews/title/${id}`);
            setReviews(rRes.data.data);
        } catch (err) { console.error(err); }
    }, [id]);

    useEffect(() => { fetchData(); }, [fetchData]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            await api.post('/reviews', { titleId: id, rating, text: reviewText });
            setReviewText('');
            fetchData(); 
        } catch (err) { alert('Failed to post review'); }
    };

    if (!title) return <h2 style={{textAlign:'center', padding:'50px'}}>Loading...</h2>;

    return (
        <div className="container">
            {/* Movie Info */}
            <div style={{ display: 'flex', gap: '30px', marginBottom: '40px' }}>
                <img src={title.poster} alt={title.name} style={{ width: '250px', borderRadius: '10px', border: '4px solid white' }} />
                <div>
                    <h1>{title.name}</h1>
                    <p style={{ fontSize: '1.2rem', color: '#ff69b4' }}>{title.year} • {title.type}</p>
                    <p>{title.synopsis}</p>
                </div>
            </div>

            {/* Reviews Section */}
            <div style={{ background: 'white', padding: '30px', borderRadius: '15px' }}>
                <h2>Reviews</h2>

                {/* REVIEW FORM */}
                {isAuthenticated ? (
                    <form onSubmit={handleSubmit} style={{ background: '#fff0f5', padding: '20px', borderRadius: '10px', marginBottom: '20px' }}>
                        <h3>Leave a Review</h3>
                        <div style={{ marginBottom: '10px' }}>
                            <label style={{ marginRight: '10px' }}>Rating:</label>
                            <select value={rating} onChange={(e) => setRating(e.target.value)} style={{ width: '60px' }}>
                                {[10,9,8,7,6,5,4,3,2,1].map(n => <option key={n} value={n}>{n}</option>)}
                            </select>
                        </div>
                        <textarea 
                            value={reviewText} 
                            onChange={(e) => setReviewText(e.target.value)} 
                            placeholder="Write your thoughts..." 
                            required 
                            style={{ width: '100%', height: '80px' }} 
                        />
                        <button type="submit" className="btn" style={{ marginTop: '10px' }}>Post</button>
                    </form>
                ) : (
                    <p><Link to="/login" style={{color: '#ff69b4', fontWeight: 'bold'}}>Log in</Link> to leave a review!</p>
                )}

                {/* REVIEW LIST */}
                {reviews.map(r => (
                    <div key={r._id} style={{ borderBottom: '1px solid #eee', padding: '10px 0' }}>
                        <strong>{r.userId?.username}</strong> <span style={{color:'#ff69b4'}}>★ {r.rating}/10</span>
                        <p>{r.text}</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default TitleDetailsPage;