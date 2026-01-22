---
name: backend-api
description: Build backend APIs with clean routes, request/response handling, and database integration.
---

# Backend API Development

## Instructions

1. **Project setup**
   - Initialize server (Node.js / Express)
   - Configure environment variables
   - Organize folders (routes, controllers, models)

2. **Routing**
   - Create RESTful routes (GET, POST, PUT, DELETE)
   - Separate routes from business logic
   - Use meaningful endpoint names

3. **Request & Response Handling**
   - Validate incoming request data
   - Handle query params, body, and headers
   - Send proper HTTP status codes and JSON responses

4. **Database Integration**
   - Connect to database (MongoDB / PostgreSQL / MySQL)
   - Define schemas or models
   - Perform CRUD operations securely

5. **Error Handling**
   - Centralized error middleware
   - Handle async errors gracefully
   - Return consistent error responses

## Best Practices
- Follow REST conventions
- Keep controllers thin and reusable
- Never expose sensitive data
- Use async/await for readability
- Validate and sanitize user input

## Example Structure
```js
// server.js
import express from "express";
import mongoose from "mongoose";
import userRoutes from "./routes/user.routes.js";

const app = express();

app.use(express.json());
app.use("/api/users", userRoutes);

mongoose.connect(process.env.MONGO_URI);

app.listen(3000, () => {
  console.log("Server running on port 3000");
});
