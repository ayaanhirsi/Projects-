## Full-Stack Web App: Anime/Movie Recommendation Hub
This project is a full-stack page application, Users can browse, authenticate, and submit reviews for titles.
- Project Topic: Anime / Movie Recommendation Hub
- Front-End Framework: React (Vite)
- Backend Stack: Node.js, Express.js, MongoDB (Mongoose)
- Security: JWT-based authentication, bcryptjs for password hashing.
- Core Entities: Titles (Read, Filter) and Reviews (Create, Read).

## Architecture and Data Model

1.1. Entity Relationship Diagram (ERD)

The application uses three core collections demonstrating the required data relationship.
<img width="1024" height="1024" alt="image" src="https://github.com/user-attachments/assets/0afc9703-bd7f-4bbd-8b75-b4522c988220" />


The diagram above illustrates the One-to-Many (1:N) relationship between both the User and Title collections and the central Review collection.

1.2. Mongoose Data Models 

Entity: User
- _id: ObjectId (Primary Key)
- username: String (required, unique)
- email: String (required, unique, lowercase)
- passwordHash: String (Hashed via bcryptjs hook)
- role: String (enum: 'user', 'admin', default: 'user')

Entity: Title
- _id: ObjectId (Primary Key)
- name: String (required, Indexed for search)
- type: String (enum: 'movie', 'anime', 'tv', required)
- genres: [String] (Array of genres)
- year: Number (required)
- poster: String (URL for image display)

Entity: Review
- _id: ObjectId (Primary Key)
- userId: ObjectId (Foreign Key, references User, 1:N Relationship)
- titleId: ObjectId (Foreign Key, references Title, 1:N Relationship)
- rating: Number (required, min: 1, max: 10)
- text: String (Review content)
   
# How to Run
2.1. Server Setup (assignment02/server/)
- Navigate to the server/ directory.
- Install dependencies: npm install
- Seed the database: npm run seed
- Create a file named .env and configure MONGODB_URI, JWT_SECRET, and PORT=5000.
- Start the API: npm run dev

4.2. Client Setup (assignment02/client/)
- Navigate to the client/ directory.
- Install dependencies: npm install
- Create a file named .env and set VITE_API_BASE_URL=http://localhost:5000/api.
- Start the client: npm run dev
- Access the app at http://localhost:5173.

5. Reflection and Conclusion
5.1. Major Challenges and Fixes
   
- Authentication Stability: The server crashed during user registration due to the native bcrypt library failing and an outdated
-  Mongoose pre('save') hook. Fix: This was resolved by switching to bcryptjs and modernizing the Mongoose middleware syntax.
- API Integration: Initial pages showed "Failed to load" errors because the backend lacked the corresponding controllers/routes. Fix: Full CRUD implementation was added incrementally for Titles and Reviews, and the title controller was updated to handle dynamic search filtering from the frontend query parameters.

5.2. What I Learned

- Asynchronous Middleware: Reinforced the critical difference between synchronous and asynchronous Mongoose middleware (pre hooks) and the necessity of returning a promise or using async/await correctly.
- Full-Stack Debugging: Gained experience tracing network errors (404/500) from the client's console back to the server logs (backend crash) to pinpoint the source of the failure.


