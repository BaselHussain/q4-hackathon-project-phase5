---
name: auth-skill
description: Implement secure authentication systems including signup, signin, password hashing, JWT tokens, and Better Auth integration.
---

# Authentication Skill

## Instructions

1. **User Authentication Flow**
   - User signup with validated inputs
   - Secure user signin
   - Session or token-based authentication
   - Proper logout handling

2. **Password Security**
   - Hash passwords before storing
   - Use modern hashing algorithms (bcrypt, argon2)
   - Never store plain-text passwords
   - Apply salting automatically

3. **JWT Token Handling**
   - Generate access tokens on signin
   - Include user identity and roles in payload
   - Set token expiration
   - Verify token on protected routes

4. **Better Auth Integration**
   - Configure Better Auth provider
   - Connect with database
   - Enable email/password or OAuth
   - Handle callbacks and sessions

5. **Protected Routes**
   - Middleware-based route protection
   - Role-based access control (optional)
   - Token validation on each request

## Best Practices
- Always hash passwords
- Use environment variables for secrets
- Keep JWT expiry short
- Refresh tokens securely
- Return clear but safe error messages
- Follow OWASP authentication guidelines

## Example Structure
```ts
// Signup
const hashedPassword = await bcrypt.hash(password, 10);

// JWT Creation
const token = jwt.sign(
  { userId: user.id },
  process.env.JWT_SECRET,
  { expiresIn: "1h" }
);

// Protected Route
app.get("/dashboard", verifyToken, (req, res) => {
  res.json({ message: "Access granted" });
});
