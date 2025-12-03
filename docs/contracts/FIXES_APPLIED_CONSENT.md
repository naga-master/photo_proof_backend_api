# Fixes Applied - Consent Implementation

**Date:** November 26, 2024  
**Status:** ✅ All errors fixed

---

## Errors Fixed

### 1. Frontend Import Error ❌ → ✅

**Error:**
```
Failed to resolve import "../services/api" from "src/pages/PrivacySettings.tsx"
```

**Root Cause:**
- `PrivacySettings.tsx` and `ConsentScreen.tsx` were trying to import a non-existent `api` service
- The project uses axios directly, not a centralized api service

**Fix Applied:**
Updated 2 files to use axios directly:

**File: `Photo_Proof_v1/src/pages/PrivacySettings.tsx`**
```typescript
// Before:
import api from '../services/api';

// After:
import axios from 'axios';
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

Updated all API calls:
```typescript
// Before:
await api.get('/v2/data-rights/privacy-settings');

// After:
const token = localStorage.getItem('token');
await axios.get(`${API_BASE_URL}/v2/data-rights/privacy-settings`, {
  headers: { Authorization: `Bearer ${token}` },
});
```

**File: `Photo_Proof_v1/src/components/ConsentScreen.tsx`**
```typescript
// Before:
import api from '../services/api';

// After:
import axios from 'axios';
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

---

### 2. Backend Import Errors ❌ → ✅

**Error 1:**
```python
ImportError: cannot import name 'get_db' from 'app.db.base'
```

**Root Cause:**
- `data_rights.py` was trying to import `get_db` from `app.db.base`
- But `get_db` is actually defined in `app.db.session`

**Fix Applied:**
```python
# Before:
from ..db.base import get_db

# After:
from ..db.session import get_db
```

---

**Error 2:**
```python
ModuleNotFoundError: No module named 'app.auth'
```

**Root Cause:**
- `data_rights.py` was trying to import `get_current_user` from `..auth`
- But `get_current_user` is actually in `..core.dependencies`

**Fix Applied:**
```python
# Before:
from ..auth import get_current_user

# After:
from ..core.dependencies import get_current_user
```

---

**Error 3: Type Compatibility**

**Problem:**
- `get_current_user` returns `UserRead` (Pydantic schema)
- But we were using `User` (SQLAlchemy model) type annotation
- Code tried to modify `current_user` attributes directly (not allowed on Pydantic models)

**Fix Applied:**

1. Changed all function signatures:
```python
# Before:
async def some_function(
    current_user: User = Depends(get_current_user),
)

# After:
async def some_function(
    current_user: UserRead = Depends(get_current_user),
)
```

2. Fetch User model when updates needed:
```python
# Before (would fail - can't modify Pydantic schema):
current_user.name = "New Name"
db.commit()

# After (correct - fetch and modify SQLAlchemy model):
user_model = db.query(User).filter(User.id == current_user.id).first()
if user_model:
    user_model.name = "New Name"
    db.commit()
```

This pattern was applied in:
- `update_consent()` - Update consent fields
- `correct_user_data()` - Update name/email/phone
- `request_account_deletion()` - Verify password and anonymize user

---

**Error 4: 404 Not Found on Consent Endpoint**

**Problem:**
```
PUT http://localhost:8000/v2/data-rights/consent 404 (Not Found)
```

**Root Cause:**
- The router had a prefix defined: `APIRouter(prefix="/data-rights")`
- The router was also registered with a prefix: `include_router(..., prefix="/v2/data-rights")`
- This created a duplicate path: `/v2/data-rights/data-rights/consent` ❌

**Fix Applied:**
```python
# Before:
router = APIRouter(prefix="/data-rights", tags=["Data Rights"])
# Would create: /v2/data-rights/data-rights/consent

# After:
router = APIRouter(tags=["Data Rights"])
# Creates: /v2/data-rights/consent ✅
```

**Result:** All endpoints now accessible at correct paths:
- ✅ `/v2/data-rights/consent`
- ✅ `/v2/data-rights/summary`
- ✅ `/v2/data-rights/export`
- ✅ `/v2/data-rights/delete-account`
- etc.

---

## Files Modified

### Frontend (3 files):
1. ✅ `Photo_Proof_v1/src/components/ConsentScreen.tsx`
   - Removed `import api` 
   - Added `import axios` and `API_BASE_URL`
   - Added token authorization to API calls
   - Removed unused `useNavigate` import

2. ✅ `Photo_Proof_v1/src/pages/PrivacySettings.tsx`
   - Removed `import api`
   - Added `import axios` and `API_BASE_URL`
   - Updated 4 API calls with axios + Bearer token

3. ✅ `Photo_Proof_v1/src/pages/PrivacyPolicy.tsx` (no changes, already correct)

### Backend (1 file):
1. ✅ `photo_proof_api/app/routers/data_rights.py`
   - Fixed import path for `get_db` (from `..db.session` not `..db.base`)
   - Fixed import path for `get_current_user` (from `..core.dependencies` not `..auth`)
   - Changed all function signatures to use `UserRead` instead of `User`
   - Added User model fetching when database updates are needed
   - Fixed password verification to fetch User model first
   - **Removed duplicate prefix** - Changed `APIRouter(prefix="/data-rights")` to `APIRouter()` to avoid double prefix

---

## Verification

### What Should Work Now:

**Frontend:**
✅ ConsentScreen component loads without errors  
✅ PrivacySettings page loads without errors  
✅ All API calls include proper Bearer token authentication  
✅ Vite dev server starts successfully  

**Backend:**
✅ `data_rights` router imports successfully  
✅ All 9 API endpoints available at `/v2/data-rights/*`  
✅ FastAPI server starts without import errors  

---

## Testing Checklist

**Frontend Tests:**
- [ ] Start Vite dev server: `npm run dev`
- [ ] Navigate to consent screen (after login if no consent)
- [ ] Click consent checkboxes
- [ ] Submit consent form
- [ ] Verify no console errors
- [ ] Navigate to Settings → Privacy
- [ ] Toggle consent preferences
- [ ] Click "Export My Data"
- [ ] Try account deletion

**Backend Tests:**
- [ ] Start FastAPI server: `./start.sh`
- [ ] Check logs for no import errors
- [ ] Visit http://localhost:8000/docs
- [ ] Verify `/v2/data-rights/*` endpoints visible
- [ ] Test GET `/v2/data-rights/consent` (with Bearer token)
- [ ] Test PUT `/v2/data-rights/consent` (with Bearer token)

**Integration Tests:**
- [ ] Login as studio owner → See consent screen
- [ ] Agree to consent → Navigate to dashboard
- [ ] Logout and login again → No consent screen (already consented)
- [ ] Go to Settings → Privacy → See preferences
- [ ] Toggle marketing emails → Verify update successful
- [ ] Export data → Download file successfully

---

## API Authentication Pattern

All data rights endpoints now use this pattern:

```typescript
const token = localStorage.getItem('token');
const response = await axios.METHOD(`${API_BASE_URL}/endpoint`, 
  { /* request body */ },
  { headers: { Authorization: `Bearer ${token}` } }
);
```

**Endpoints using this pattern:**
- ✅ GET `/v2/data-rights/consent`
- ✅ PUT `/v2/data-rights/consent`
- ✅ GET `/v2/data-rights/privacy-settings`
- ✅ POST `/v2/data-rights/export`
- ✅ POST `/v2/data-rights/delete-account`

---

## Environment Variables

Make sure these are set:

**Frontend (.env or .env.local):**
```bash
VITE_API_URL=http://localhost:8000
```

**Backend (.env):**
```bash
DATABASE_URL=sqlite:///photo_proof.db
SECRET_KEY=your-secret-key-here
```

---

## Next Steps

1. ✅ **Start servers:**
   ```bash
   # Terminal 1 - Backend
   cd photo_proof_api
   ./start.sh
   
   # Terminal 2 - Frontend
   cd Photo_Proof_v1
   npm run dev
   ```

2. ✅ **Test consent flow:**
   - Create new test account
   - Verify consent screen appears
   - Submit consent
   - Verify navigation to dashboard

3. ✅ **Test privacy settings:**
   - Go to Settings → Privacy
   - Verify data summary displays
   - Toggle consent preferences
   - Export data
   - Test account deletion

4. ⏰ **Get legal review:**
   - Find Indian IT lawyer
   - Send Privacy Policy for review
   - Send Terms of Service for review
   - Update with actual business info

---

## Status: ✅ Ready for Testing

All import errors fixed. Both frontend and backend should now start and run without errors.

**Estimated time to test:** 30-45 minutes  
**Next milestone:** User acceptance testing → Lawyer review → Production deployment
