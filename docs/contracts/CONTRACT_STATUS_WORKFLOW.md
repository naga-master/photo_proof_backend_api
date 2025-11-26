# Contract Status Workflow

**Date:** November 26, 2024  
**Purpose:** Explain when and how contract statuses change

---

## Contract Statuses

There are **6 possible statuses** for a contract:

1. **draft** - Initial status when created
2. **sent** - When sent to client for signature
3. **viewed** - When client opens/views the contract
4. **signed** - When client signs the contract
5. **expired** - When contract passes expiration date without being signed
6. **cancelled** - When studio cancels the contract

---

## Status Flow Diagram

```
┌─────────┐
│  DRAFT  │ ← Contract created
└────┬────┘
     │
     │ Studio clicks "Send to Client"
     │ API: POST /v2/contracts/{id}/send
     ▼
┌─────────┐
│  SENT   │ ← Email sent to client
└────┬────┘
     │
     │ Client opens contract link
     │ API: GET /v2/contracts/{id}
     ▼
┌─────────┐
│ VIEWED  │ ← Client has seen the contract
└────┬────┘
     │
     │ Client signs contract
     │ API: POST /v2/contracts/{id}/sign
     ▼
┌─────────┐
│ SIGNED  │ ← Contract completed ✓
└─────────┘

Alternative flows:
- DRAFT/SENT/VIEWED → CANCELLED (studio cancels)
- DRAFT/SENT/VIEWED → EXPIRED (expiration date passes)
```

---

## Detailed Status Transitions

### 1. DRAFT → SENT

**When:** Studio sends contract to client  
**How:** Click "Send Contract" button in UI  
**API:** `POST /v2/contracts/{contract_id}/send?recipient_email=client@example.com`

**What happens:**
```python
# In contract_service.py, line 345
contract.status = "sent"
contract.sent_at = datetime.utcnow()
```

**Requirements:**
- Contract must be in `draft`, `sent`, or `viewed` status
- Only studio users can send contracts
- Must provide recipient email

**Result:**
- Status changes to `sent`
- `sent_at` timestamp recorded
- Email sent to client with contract link
- Activity logged

---

### 2. SENT → VIEWED

**When:** Client opens the contract link  
**How:** Client clicks email link and views contract  
**API:** `GET /v2/contracts/{contract_id}`

**What happens:**
```python
# In contracts.py, line 346-347
if contract.status == "sent" and not contract.viewed_at:
    contract.status = "viewed"
    contract.viewed_at = datetime.utcnow()
```

**Requirements:**
- Contract must be in `sent` status
- First time viewing (viewed_at is None)

**Result:**
- Status changes to `viewed`
- `viewed_at` timestamp recorded
- Client can now see contract details

---

### 3. VIEWED → SIGNED (or SENT → SIGNED)

**When:** Client signs the contract  
**How:** Client draws signature and clicks "Sign Contract"  
**API:** `POST /v2/contracts/{contract_id}/sign`

**What happens:**
```python
# In contract_service.py, line 385
contract.status = "signed"
contract.signed_at = datetime.utcnow()
contract.client_signature = signature_data
contract.client_signature_hash = signature_hash
contract.client_ip = client_info['ip']
contract.client_user_agent = client_info['user_agent']
```

**Requirements:**
- Contract must be in `sent` or `viewed` status
- Contract must not be expired
- Valid signature data required

**Payload:**
```json
{
  "signature": "data:image/png;base64,iVBORw0KGg..."
}
```

**Result:**
- Status changes to `signed`
- `signed_at` timestamp recorded
- Signature image saved
- Signature hash generated (SHA-256)
- Client IP and user agent recorded
- Signed PDF generated with signature
- Activity logged

---

### 4. ANY → CANCELLED

**When:** Studio manually cancels contract  
**How:** Click "Cancel Contract" in UI  
**API:** `POST /v2/contracts/{contract_id}/cancel` (needs implementation)

**Currently:** Not fully implemented in the codebase

**Would require:**
```python
contract.status = "cancelled"
contract.cancelled_at = datetime.utcnow()
contract.cancellation_reason = reason
```

---

### 5. ANY → EXPIRED

**When:** Contract expiration date passes without being signed  
**How:** Automatic check (needs background job)

**Currently:** Checked at signing time:
```python
# In contract_service.py, line 372-373
if contract.expires_at and contract.expires_at < datetime.utcnow():
    raise ValueError("Contract has expired")
```

**Needs Implementation:**
- Background job to check expired contracts daily
- Automatically update status to `expired`

---

## Current Implementation Status

### ✅ Fully Implemented:
1. **DRAFT creation** - When contract is created
2. **DRAFT → SENT** - When sending to client
3. **SENT → VIEWED** - When client opens link
4. **VIEWED/SENT → SIGNED** - When client signs

### ⚠️ Partially Implemented:
1. **EXPIRED status** - Checked but not automatically set
2. **CANCELLED status** - Status exists but no API endpoint

### ❌ Not Implemented:
1. Background job to mark expired contracts
2. Cancel contract endpoint
3. Re-send contract functionality

---

## How to Use in Your App

### For Studio (Backend UI):

#### 1. Create Contract (Status: DRAFT)
```typescript
// Already works!
const contract = await contractService.createContract({
  client_id: 7,
  title: "Wedding Photography Contract",
  content: "Terms...",
  expires_days: 30
});
// Status: "draft"
```

#### 2. Send Contract (Status: DRAFT → SENT)
```typescript
// Need to implement in UI
const sendContract = async (contractId: string, email: string) => {
  const response = await fetch(`/v2/contracts/${contractId}/send?recipient_email=${email}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  // Status changes to: "sent"
};
```

**UI Flow:**
1. View contract in list
2. Click "Send to Client" button
3. Confirm email address
4. Contract sent, status → `sent`

#### 3. Track Status
```typescript
// List shows status
const contracts = await contractService.getContracts();
contracts.forEach(contract => {
  console.log(`${contract.title}: ${contract.status}`);
  // "Wedding Contract: sent"
  // "Portrait Contract: signed"
});
```

### For Client (Mobile/Web App):

#### 1. View Contract (Status: SENT → VIEWED)
```typescript
// Client receives email with link
// Clicks: https://app.com/contracts/3574720e-c842-420a-a37d-e754dd76e3de

// When they open it:
const contract = await fetch(`/v2/contracts/${contractId}`);
// Status automatically changes to: "viewed"
```

#### 2. Sign Contract (Status: VIEWED → SIGNED)
```typescript
// Client draws signature on canvas
const signatureData = signatureCanvas.toDataURL();

// Submit signature
const response = await fetch(`/v2/contracts/${contractId}/sign`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    signature: signatureData
  })
});
// Status changes to: "signed"
```

---

## Implementation Checklist

### To Complete the Workflow:

#### 1. Add "Send Contract" Button to UI ✅ Needed
**File:** `Photo_Proof_v1/components/ContractsPage.tsx`

Add button to contract list:
```tsx
<button 
  onClick={() => handleSendContract(contract.id, contract.client.email)}
  disabled={contract.status === 'signed'}
>
  {contract.status === 'draft' ? 'Send to Client' : 'Resend'}
</button>
```

#### 2. Add Send Contract Modal ✅ Needed
Show modal to confirm email before sending:
```tsx
<SendContractModal
  contract={selectedContract}
  onSend={(email) => sendContract(contract.id, email)}
/>
```

#### 3. Add Status Badge Component ✅ Needed
Show visual status in contracts list:
```tsx
<StatusBadge status={contract.status}>
  {/* 
    draft: gray
    sent: blue
    viewed: yellow
    signed: green
    expired: red
    cancelled: gray
  */}
</StatusBadge>
```

#### 4. Add Expiration Check Job ⚠️ Future
Background job to mark expired contracts:
```python
# Add to cron/scheduler
async def check_expired_contracts():
    contracts = db.query(Contract).filter(
        Contract.expires_at < datetime.utcnow(),
        Contract.status.in_(['draft', 'sent', 'viewed'])
    ).all()
    
    for contract in contracts:
        contract.status = 'expired'
    
    db.commit()
```

#### 5. Add Cancel Contract Endpoint ⚠️ Future
```python
@router.post("/{contract_id}/cancel")
async def cancel_contract(
    contract_id: str,
    reason: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    contract.status = "cancelled"
    contract.cancelled_at = datetime.utcnow()
    # ...
```

---

## FAQ

### Q: Why is my contract stuck in "draft"?
**A:** You need to click "Send to Client" to move it to "sent" status. This button needs to be added to the UI.

### Q: Can I skip "sent" and go directly to "signed"?
**A:** No, contracts must be sent to client first. The client signs via their own interface.

### Q: What happens if contract expires?
**A:** Currently, the contract cannot be signed after expiration, but status doesn't automatically update to "expired". Needs background job.

### Q: Can I edit a sent contract?
**A:** Not implemented yet. Would need to create a new version or cancel and recreate.

### Q: How does client get the contract link?
**A:** When you send the contract (status → sent), an email is sent to the client with a link. Currently needs email service implementation.

---

## Next Steps

### Immediate (High Priority):
1. **Add "Send Contract" button** to contracts list in UI
2. **Implement send contract modal** with email confirmation
3. **Add status badges** to show contract status visually
4. **Test sending workflow** end-to-end

### Short Term (Medium Priority):
1. Implement email sending (currently returns True but doesn't send)
2. Add contract detail view for clients
3. Add signature canvas component for clients
4. Test signing workflow end-to-end

### Long Term (Low Priority):
1. Background job for expired contracts
2. Cancel contract functionality
3. Contract versioning
4. Edit sent contracts
5. Resend contract with modifications

---

## Summary

**Status Changes:**
- **DRAFT** → Created (automatic)
- **SENT** → When you click "Send to Client" (manual action needed)
- **VIEWED** → When client opens link (automatic)
- **SIGNED** → When client signs (client action)

**Current Gap:** 
You need to add a "Send Contract" button to the UI to transition from DRAFT → SENT.

**Recommendation:**
1. Add send button to contracts list
2. Test sending a contract
3. Client will then be able to sign it
4. Status will update automatically through the workflow
