# CSRF Protection Guide

## What is CSRF Protection?

Cross-Site Request Forgery (CSRF) is a type of security vulnerability where unauthorized commands are submitted from a user that the web application trusts. CSRF protection helps prevent this by ensuring that form submissions come from legitimate sources.

## How CSRF Protection Works in This Application

1. The server generates a unique CSRF token for each user session.
2. This token is included in forms as a hidden field.
3. When a form is submitted, the server validates that the token is correct.
4. If the token is missing or invalid, the request is rejected.

## Adding CSRF Tokens to Forms

For any form that uses POST, PUT, PATCH, or DELETE methods, you **must** include a CSRF token.

Add this line inside your `<form>` tag:

```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

For example:

```html
<form method="POST" action="/some-endpoint">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  <!-- Your other form fields go here -->
  <button type="submit">Submit</button>
</form>
```

## Why Was the Login Form Not Working?

The login form was failing because:

1. CSRF protection was enabled at the application level.
2. The login form was submitting without a CSRF token.
3. The server rejected the form submission as potentially fraudulent.

## Troubleshooting CSRF Issues

If you encounter "CSRF token missing" or "Invalid CSRF token" errors:

1. Ensure every form includes the hidden CSRF token field.
2. For forms generated dynamically with JavaScript, ensure they also include the token.
3. Make sure your session cookie is being set correctly.
4. Check that your form action is correct and pointing to the right endpoint.

## For AJAX Requests

For AJAX POST/PUT/PATCH/DELETE requests, you need to include the CSRF token in the headers:

```javascript
fetch('/some-endpoint', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRFToken': '{{ csrf_token() }}'
  },
  body: JSON.stringify(data)
})
```

## Forms That Need CSRF Tokens (Incomplete List)

Many forms in the application need CSRF tokens, including:

- Login form
- Add Entry form
- All Formula Ford forms
- All management forms
- Checklist forms
- Import/export forms

**IMPORTANT:** Double-check all forms that use POST, PUT, PATCH, or DELETE methods to ensure they include CSRF tokens. 