import React, { useState, useEffect, useCallback } from 'react';
import api from '../services/api'; 
import { Link } from 'react-router-dom';

const BrowsePage = () => {
    const [titles, setTitles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [page, setPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [filter, setFilter] = useState({ search: '', type: '', genre: '' });

    const fetchTitles = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const query = new URLSearchParams({
                page: page,
                limit: 10, 
                search: filter.search,
                type: filter.type,
                genre: filter.genre
            }).toString();

            const response = await api.get(`/titles?${query}`);
            
            setTitles(response.data.data);
            setTotalPages(response.data.meta.totalPages);

        } catch (err) {
            console.error('API Error:', err);
            setError('Failed to load titles. Please check the backend server.');
        } finally {
            setLoading(false);
        }
    }, [page, filter]); 

    useEffect(() => {
        fetchTitles();
    }, [fetchTitles]);

    const handleFilterChange = (e) => {
        setFilter({ ...filter, [e.target.name]: e.target.value });
        setPage(1); 
    };

    const handleSearchSubmit = (e) => {
        e.preventDefault();
        setPage(1);
        fetchTitles(); 
    };
    
    if (loading) return <h2 style={{textAlign: 'center', padding: '50px'}}>Loading Movies...</h2>;
    if (error) return <h2 style={{color: 'red', textAlign: 'center', padding: '50px'}}>{error}</h2>;

    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px' }}>
            <h2>Browse All Titles</h2>

            {/* --- Search and Filter UI --- */}
            <form onSubmit={handleSearchSubmit} style={{ marginBottom: '20px', display: 'flex', gap: '10px' }}>
                <input
                    type="text"
                    name="search"
                    placeholder="Search by name..."
                    value={filter.search}
                    onChange={handleFilterChange}
                    style={{ flexGrow: 1, padding: '8px' }}
                />
                <select name="type" onChange={handleFilterChange} style={{ padding: '8px' }}>
                    <option value="">All Types</option>
                    <option value="movie">Movie</option>
                    <option value="anime">Anime</option>
                    <option value="tv">TV Series</option>
                </select>
            
                <button type="submit" style={{ padding: '8px 15px', backgroundColor: '#5cb85c', color: 'white', border: 'none', cursor: 'pointer' }}>Search</button>
            </form>

            {/* --- Title List --- */}
            <div className="title-list" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '20px' }}>
                {titles.length > 0 ? (
                    titles.map(title => (
                        <div key={title._id} style={{ border: '1px solid #ccc', padding: '15px', borderRadius: '8px' }}>
                            <Link to={`/titles/${title._id}`} style={{ textDecoration: 'none', color: 'black' }}>
                                <h3>{title.name} ({title.year})</h3>
                            </Link>
                            <p><strong>Type:</strong> {title.type}</p>
                            <p><strong>Genres:</strong> {title.genres.join(', ')}</p>
                            <p>{title.synopsis.substring(0, 100)}...</p>
                        </div>
                    ))
                ) : (
                    <p style={{ gridColumn: '1 / -1', textAlign: 'center' }}>No titles found matching your criteria.</p>
                )}
            </div>

            {/* --- Pagination Controls (Required for Assignment) --- */}
            <div style={{ marginTop: '30px', textAlign: 'center' }}>
                <button 
                    onClick={() => setPage(p => p - 1)} 
                    disabled={page <= 1 || loading}
                    style={{ padding: '10px', marginRight: '10px' }}
                >
                    Previous
                </button>
                <span>Page {page} of {totalPages}</span>
                <button 
                    onClick={() => setPage(p => p + 1)} 
                    disabled={page >= totalPages || loading}
                    style={{ padding: '10px', marginLeft: '10px' }}
                >
                    Next
                </button>
            </div>
        </div>
    );
};

export default BrowsePage;