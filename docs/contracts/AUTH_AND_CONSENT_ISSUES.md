# Authentication and Consent Issues - Diagnosis

**Date:** November 26, 2024  
**Status:** ⚠️ Pre-existing authentication issue blocking consent flow

---

## The Core Problem

You're experiencing a **pre-existing authentication issue** that's unrelated to the DPDPA consent implementation. The token isn't being saved to localStorage after login, causing all authenticated API calls to fail with 401 errors.

---

## Evidence from Logs

```
[API Client] No token found in localStorage
POST http://localhost:8000/api/auth/refresh 401 (Unauthorized)
GET http://localhost:8000/v2/invoices/ 401 (Unauthorized)
GET http://localhost:8000/v2/contracts/?limit=50 401 (Unauthorized)
```

**What this means:**
- ❌ Login isn't saving token to localStorage
- ❌ All authenticated endpoints fail with 401
- ❌ This breaks EVERYTHING, not just consent

---

## Why You Don't See Consent Screen

**Current Flow:**
1. ✅ You login successfully (backend validates credentials)
2. ❌ Token NOT saved to localStorage (BUG in existing auth system)
3. ✅ AuthContext says you're authenticated (from response)
4. ✅ App navigates to dashboard
5. ⚠️ Consent check tries to verify via API
6. ❌ Gets 401 error (no valid token)
7. ⚠️ My code interprets 401 as "needs consent" (after my latest fix)
8. ✅ Should show consent screen now
9. ❌ But when you submit consent, also gets 401 (no token)

**Result:** You're in a broken auth state where the app thinks you're logged in, but you have no valid token.

---

## Root Cause: Existing Authentication Bug

This is **NOT caused by the DPDPA/consent implementation**. This is a pre-existing bug in your authentication system.

### Symptoms:
1. Login appears to work (you see dashboard)
2. But token not in localStorage
3. All API calls fail with 401
4. Token refresh also fails with 401

### Likely Causes:
1. **Login endpoint not returning token in expected format**
2. **AuthContext/AuthService not saving token to localStorage**
3. **Token being saved to wrong key**
4. **Token being cleared immediately after save**

---

## Quick Diagnosis

Let me check what's happening during login:

<function_calls>
<invoke name="Read">
<parameter name="file_path">/Users/ns632@apac.comcast.com/Documents/v0_photo_proof/Photo_Proof_v1/contexts/AuthContext.tsx
