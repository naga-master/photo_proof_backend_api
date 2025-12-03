# Contracts Feature - Troubleshooting Guide

## ✅ What's Been Done

1. **Backend API** - ✅ Fully implemented with 15+ endpoints
2. **Database** - ✅ Tables created and migrated
3. **Test Data** - ✅ 5 sample contracts created:
   - 1 Draft
   - 1 Sent
   - 1 Viewed
   - 2 Signed

4. **Web Frontend** - ✅ Fully implemented:
   - Contracts page in top navigation
   - Contracts page in studio dashboard sidebar
   - Contract viewer with signature pad
   - Statistics dashboard

## ❌ 403 Forbidden Error - SOLUTION

The 403 error means you're either:
1. Not logged in
2. Logged in as a CLIENT (clients can't access studio features)
3. Missing auth token

### Fix: Login as Studio User

**Step 1: Check Your Current Login**
Open browser console (F12) and run:
```javascript
console.log('Role:', localStorage.getItem('user_role'));
console.log('Token exists:', !!localStorage.getItem('auth_token'));
```

**Step 2: If Role is "client" or null:**
1. Click "Logout" button
2. Login with **STUDIO credentials** (not client credentials)
   - Username: `studio` or `admin` or your studio username
   - Password: Your studio password

**Step 3: After Studio Login**
1. You should see the Studio Dashboard
2. Click "Contracts" in the left sidebar
3. You should now see 5 test contracts!

## 📄 "Contract Creation Coming Soon" - EXPLANATION

The "New Contract" button currently shows an alert because:
- The UI is ready but the contract creation FORM hasn't been built yet
- You can create contracts via:
  1. **API directly** (using Swagger docs at http://localhost:8000/docs)
  2. **Postman/curl**
  3. **Python script** (like the test script)

### To Create a Contract via API:

1. Go to http://localhost:8000/docs
2. Find POST `/v2/contracts`
3. Click "Try it out"
4. Fill in:
```json
{
  "client_id": "1",
  "title": "My New Contract",
  "content": "Contract content here...",
  "send_immediately": false
}
```
5. Click "Execute"

## 🔧 Full Testing Checklist

### Backend Check
```bash
# 1. Check API is running
ps aux | grep uvicorn

# 2. Check test data
cd photo_proof_api
sqlite3 photo_proof.db "SELECT count(*) FROM contracts;"
# Should return: 5

# 3. Start API if needed
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Check
```bash
# 1. Start web app
cd Photo_Proof_v1
npm run dev

# 2. Open browser: http://localhost:5173
# 3. Login as STUDIO user
# 4. Click "Contracts" in sidebar or top nav
```

### Browser Console Check
```javascript
// Check authentication
localStorage.getItem('auth_token')
localStorage.getItem('user_role')  // Must be: studio_owner, studio_admin, or studio_photographer

// Manual API test
fetch('http://localhost:8000/v2/contracts/stats', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
  }
})
.then(r => r.json())
.then(console.log)
.catch(console.error)
```

## 📍 Where to Access Contracts

### For Studio Users:
**Option 1: Studio Dashboard (Sidebar)**
1. Login as studio user
2. Look at left sidebar
3. Click "Contracts" (5th item from top, between Invoices and Analytics)

**Option 2: Top Navigation** (when viewing as client)
1. In any page
2. Look at top navigation bar
3. Click "Contracts" (between Store and About)

### For Clients:
Clients can view contracts sent to them via:
1. Top navigation → Contracts
2. They can only see THEIR contracts
3. They can sign unsigned contracts

## 🎯 What Should Work Now

✅ View contracts list with stats
✅ Filter contracts by status (All, Draft, Sent, Viewed, Signed)
✅ Click a contract to view details
✅ Sign contracts (for sent/viewed status)
✅ Signature pad with terms agreement
✅ Beautiful UI with animations

## 🚧 What's Not Done Yet

❌ Contract creation form UI (use API for now)
❌ Email sending (structure exists, not implemented)
❌ PDF viewer (text view only)
❌ Template management UI

## 📊 Expected Data

After running the test script, you should see:

**Dashboard Stats:**
- Total: 5
- Draft: 1
- Pending (Sent + Viewed): 2
- Signed: 2
- Expiring: 0

**Contracts List:**
1. Wedding Photography - Johnson Wedding (DRAFT)
2. Portrait Session - Smith Family (SENT)
3. Corporate Headshots - Tech Corp (VIEWED)
4. Event Coverage - Charity Gala (SIGNED)
5. Product Photography - E-commerce Store (SIGNED)

## 🔑 Test Credentials

Make sure you're using **STUDIO credentials**, not client credentials:

**Studio Login:**
- Check your LOGIN_CREDENTIALS.md file
- Look for entries with role: "studio_owner" or "studio_admin"
- Username usually: `studio`, `admin`, or your studio name
  
**NOT Client Login:**
- If username is like "OldClient", "Emily", etc. - that's a CLIENT
- Clients can't access studio dashboard

## 🐛 Common Issues

### Issue: "Failed to load contracts: 403 Forbidden"
**Solution:** You're logged in as client. Logout and login as studio user.

### Issue: "No contracts found"
**Solution:** Run the test script:
```bash
cd photo_proof_api
source venv/bin/activate
python create_test_contract.py
```

### Issue: Contracts page is blank/loading forever
**Solution:** 
1. Check API is running: `ps aux | grep uvicorn`
2. Check browser console for errors
3. Verify auth token exists: `localStorage.getItem('auth_token')`

### Issue: Can't see "Contracts" in sidebar
**Solution:** You're viewing as client, not in studio dashboard. Navigate to /dashboard route or login as studio.

## 📚 API Endpoints Available

All at `http://localhost:8000/v2/contracts`:

- `GET /` - List contracts
- `GET /{id}` - Get contract details
- `POST /` - Create contract
- `PUT /{id}` - Update contract
- `DELETE /{id}` - Delete contract
- `POST /{id}/sign` - Sign contract
- `GET /{id}/verify` - Verify signature
- `GET /stats` - Get statistics
- `GET /{id}/activities` - Get activity log
- `POST /templates` - Create template
- `GET /templates` - List templates

## 🎉 Success Criteria

You know it's working when:
1. ✅ You can login as studio user
2. ✅ You see "Contracts" in the sidebar
3. ✅ You click it and see 5 contracts
4. ✅ Stats show: Total: 5, Draft: 1, Signed: 2
5. ✅ You can click a contract and see its details
6. ✅ You can click a sent/viewed contract and see "Sign Contract" button

---

## 🆘 Still Not Working?

1. **Check API logs** - Look at terminal where uvicorn is running
2. **Check browser console** - Look for red errors
3. **Check network tab** - See what requests are failing
4. **Verify database** - Run: `sqlite3 photo_proof.db "SELECT * FROM contracts LIMIT 1;"`
5. **Clear cache** - Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)

---

**Created:** 2025-11-26
**Status:** Test data created, API running, waiting for studio login to access
