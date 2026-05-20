## Assignment 2: Full-Stack Web App
Name: Ayaan Hirsi

Student ID: 173177221

Date: 2025-12-10

## Full-Stack Web App: Anime/Movie Recommendation Hub
This project is a full-stack page application  designed to meet the requirements of Assignment 02. Users can browse, authenticate, and submit reviews for titles.
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

## Screenshots
1. Home Page Screenshot
   <img width="1599" height="769" alt="Home Page Screenshot 1" src="https://github.com/user-attachments/assets/24436212-62eb-426b-8020-2ede47356e5b" />

2. Browse Page Screenshot
   <img width="1586" height="785" alt="Browse Page Screenshot 2" src="https://github.com/user-attachments/assets/95e8474a-0e31-44c6-b463-a8ce5b79e6f5" />

3. Register Page Screenshot
   <img width="1588" height="790" alt="Register Page Screenshot 3" src="https://github.com/user-attachments/assets/79ef5d17-aa24-4820-99d1-e084d5103fbb" />

4. Login Page Screenshot
   <img width="1591" height="770" alt="Login Page Screenshot 4" src="https://github.com/user-attachments/assets/90b5e858-e255-4782-ae17-412632bf7a63" />

5. Logged in Page Screenshot
<img width="1592" height="794" alt="Logged In Page Screenshot 5" src="https://github.com/user-attachments/assets/ae4e1d88-cb27-49f7-b190-47586b518ce9" />

6. Account Profile Screenshot
<img width="1591" height="785" alt="Account Profile Screenshot 6" src="https://github.com/user-attachments/assets/cf6a2226-46c1-4066-8a27-5dd002bfab25" />

7. Leaving Review Screenshot
    <img width="1584" height="776" alt="Leaving Review Screenshot 7" src="https://github.com/user-attachments/assets/bd73c69c-5051-4195-99dd-ae7336ad5745" />

8. Movie Poster Screenshot
<img width="1592" height="772" alt="Movie Poster Screenshot 8" src="https://github.com/user-attachments/assets/e1a76f0d-56ab-4ef5-9c0e-468d50066aca" />

   
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

5.3. Future Improvements

- Implement PUT and DELETE methods for user reviews.
- Develop an Admin Page for title creation and management.
