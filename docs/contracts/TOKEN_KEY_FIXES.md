# Token localStorage Key Fixes

**Date:** November 26, 2024  
**Issue:** Consent screen showing "Authentication required" after login  
**Root Cause:** Inconsistent localStorage key names for authentication token

---

## The Problem

The authentication system uses **`'auth_token'`** as the localStorage key, but several files were looking for **`'token'`** instead, causing the consent screen to not find the authentication token even after successful login.

### Files Using Wrong Key (`'token'`):
1. ❌ `App.tsx` - Consent check  
2. ❌ `ConsentScreen.tsx` - Submit consent
3. ❌ `PrivacySettings.tsx` - All data rights operations (3 occurrences)

### Files Using Correct Key (`'auth_token'`):
1. ✅ `authService.ts` - Stores token during login
2. ✅ `api-client.ts` - Reads token for API calls

---

## What Was Fixed

### 1. App.tsx
**Line 274:** Consent check fallback
```typescript
// BEFORE
const token = localStorage.getItem('token');

// AFTER  
const token = localStorage.getItem('auth_token');
```

### 2. ConsentScreen.tsx
**Line 39:** Token verification before submit
```typescript
// BEFORE
const token = localStorage.getItem('token');

// AFTER
const token = localStorage.getItem('auth_token');
```

### 3. PrivacySettings.tsx
**Lines 55, 76, 108, 143:** All API calls
```typescript
// BEFORE (4 occurrences)
const token = localStorage.getItem('token');

// AFTER (all fixed)
const token = localStorage.getItem('auth_token');
```

---

## Additional Improvements

### 1. Enhanced Logging in authService.ts
Added detailed console logs to track token storage:
```typescript
console.log('[AuthService] Storing auth data...');
console.log('[AuthService] Token received:', response.token ? `${response.token.substring(0, 20)}...` : 'NONE');
console.log('[AuthService] Token stored successfully:', storedToken ? `${storedToken.substring(0, 20)}...` : 'FAILED');
```

### 2. Enhanced Logging in ConsentScreen.tsx
Added token verification logs:
```typescript
console.log('[ConsentScreen] Token check:', token ? `${token.substring(0, 20)}...` : 'NONE');
console.log('[ConsentScreen] Submitting consent with preferences:', consents);
```

### 3. Backend Consent Check Fix
Updated `/v2/data-rights/consent` GET endpoint to return all `false` when no consent records exist:
```python
# If NO consent records exist, return all false (user needs to consent)
if not consents:
    return ConsentPreferences(
        essential=False,
        marketing_emails=False,
        sms_notifications=False,
        analytics=False,
    )
```

### 4. Debug Tool Created
Created `test-login-debug.html` for testing:
- Login flow
- Token storage verification
- Consent API testing
- localStorage inspection

---

## Expected Flow Now

1. ✅ User logs in (studio@admin.com / password123)
2. ✅ Backend returns token
3. ✅ authService stores token to `localStorage['auth_token']`
4. ✅ App checks consent via user.consent_given field (primary)
5. ✅ Fallback: App checks via API with correct token key
6. ✅ ConsentScreen shows (if no consent)
7. ✅ User clicks "I Agree - Continue"
8. ✅ ConsentScreen reads token from `localStorage['auth_token']`
9. ✅ Token found, consent submitted successfully
10. ✅ User redirected to dashboard

---

## Testing Instructions

### Option 1: Test in Browser
1. Open app: http://localhost:5173
2. Open DevTools Console
3. Login with studio@admin.com / password123
4. Watch console logs:
   - `[AuthService] Token stored successfully`
   - `[App] Checking consent for user`
   - `[ConsentScreen] Token check: eyJ...` (if consent needed)
5. Click "I Agree - Continue"
6. Should see success and redirect

### Option 2: Use Debug Tool
1. Open: `file:///Users/.../test-login-debug.html`
2. Click "Test Studio Login"
3. Check logs for token storage
4. Click "Check Token in localStorage"
5. Click "Test Consent API"

### Option 3: Manual Check
```javascript
// In browser console after login:
localStorage.getItem('auth_token')  // Should show token
localStorage.getItem('user_data')   // Should show user object
localStorage.getItem('user_role')   // Should show "studio"
```

---

## Files Modified

1. `Photo_Proof_v1/App.tsx`
2. `Photo_Proof_v1/src/components/ConsentScreen.tsx`
3. `Photo_Proof_v1/src/pages/PrivacySettings.tsx`
4. `Photo_Proof_v1/services/authService.ts`
5. `photo_proof_api/app/routers/data_rights.py`

## Files Created

1. `test-login-debug.html` - Debug tool for testing

---

## Next Steps

1. ✅ Clear browser localStorage (important!)
2. ✅ Login again with studio@admin.com
3. ✅ Verify token is stored
4. ✅ Check if consent screen appears
5. ✅ Submit consent and verify redirect

---

## Prevention

To prevent this issue in the future:

1. **Centralize token key:** Create a constant
   ```typescript
   // constants.ts
   export const TOKEN_KEY = 'auth_token';
   ```

2. **Use helper functions:**
   ```typescript
   export const getAuthToken = () => localStorage.getItem(TOKEN_KEY);
   export const setAuthToken = (token: string) => localStorage.setItem(TOKEN_KEY, token);
   ```

3. **Type-safe storage:**
   ```typescript
   interface StorageKeys {
     auth_token: string;
     user_data: string;
     user_role: string;
   }
   ```

---

**Status:** ✅ All fixes applied, ready for testing
