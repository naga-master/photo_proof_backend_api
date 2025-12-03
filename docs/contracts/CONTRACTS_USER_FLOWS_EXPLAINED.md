# Contracts & Consent - User Flows Explained

**Purpose:** Clarify when consent screens appear and how clients sign contracts  
**Date:** 2025-11-26

---

## The Two Types of Users

Your app has **TWO completely different user types**:

### 1. Studio Owner/Photographer (YOU)
- Creates account
- Uploads client photos
- Creates contracts
- Manages business
- **Role:** Service Provider

### 2. Client (Your Customer)
- Receives photos
- Views galleries
- Signs contracts
- Makes payments
- **Role:** End Consumer

**Key Point:** They have DIFFERENT workflows and DIFFERENT consent requirements!

---

## User Flow 1: Studio Owner (Photographer)

### When Studio Owner Creates Account

```
┌─────────────────────────────────────────────────┐
│              STUDIO SIGN UP                     │
└─────────────────────────────────────────────────┘

Step 1: Studio Registration
┌─────────────────────────────────────┐
│ Create Your Studio Account         │
│                                     │
│ Studio Name: [Raj Photography    ] │
│ Your Name:   [Raj Kumar          ] │
│ Email:       [raj@example.com    ] │
│ Phone:       [+91-98765-43210    ] │
│ Password:    [**********         ] │
│                                     │
│ [ Next ]                            │
└─────────────────────────────────────┘

Step 2: ⚠️ CONSENT SCREEN (DPDPA)
┌─────────────────────────────────────┐
│ Data Processing Consent            │
│                                     │
│ We will collect and process:       │
│                                     │
│ [✓] Your Business Information      │
│     • Studio name, your name       │
│     • Email, phone, address        │
│     Purpose: Account management    │
│     Required: YES                  │
│                                     │
│ [✓] Your Client Data               │
│     • Client names, emails, phones │
│     • Photos you upload            │
│     • Contracts you create         │
│     Purpose: Provide photography   │
│              services to clients   │
│     Required: YES                  │
│                                     │
│ [ ] Marketing Communications       │
│     • Product updates, tips        │
│     Purpose: Keep you informed     │
│     Required: NO                   │
│                                     │
│ Legal Notice:                      │
│ By continuing, you acknowledge:    │
│ • You are authorized to upload     │
│   client data                      │
│ • You have obtained necessary      │
│   permissions from clients         │
│ • You agree to Privacy Policy      │
│ • You agree to Terms of Service    │
│                                     │
│ [View Privacy Policy]              │
│ [View Terms of Service]            │
│                                     │
│ [✓] I agree to data processing     │
│ [✓] I confirm I have client        │
│     authorization                  │
│                                     │
│ [ Create Studio Account ]          │
└─────────────────────────────────────┘

Step 3: Account Created ✅
- Studio dashboard opens
- Can now upload photos
- Can create contracts
- Can invite clients
```

**Key Point:** Studio owner gives consent for **THEIR data + their authority to process CLIENT data**

---

## User Flow 2: Client (Your Customer)

### Scenario A: Client Gets Email Invitation

**Most Common Flow:**

```
┌─────────────────────────────────────────────────┐
│       HOW CLIENT SIGNS CONTRACT                 │
└─────────────────────────────────────────────────┘

Step 1: Studio Creates Contract
────────────────────────────────
Studio Dashboard > Contracts > New Contract
• Studio owner creates contract for "Raj Kumar"
• Fills in details
• Clicks "Send to Client"

Step 2: Client Receives Email
────────────────────────────────
📧 Email to: rajkumar@example.com

Subject: "Contract from Napster Photography"

Hi Raj Kumar,

You have received a new photography contract
from Napster Photography.

Contract: Wedding Photography - Kumar Wedding
Amount: ₹1,50,000

[Review & Sign Contract] ← Big button

This link expires in 30 days.

────────────────────────────────

Step 3: Client Clicks Link
────────────────────────────────
Link opens: https://photoproof.com/sign/abc123xyz

Option A: Public Link (No Login Required)
┌─────────────────────────────────────┐
│ Contract from Napster Photography   │
│                                     │
│ [View Contract]                     │
└─────────────────────────────────────┘

Option B: Login Required
┌─────────────────────────────────────┐
│ Sign In to View Contract            │
│                                     │
│ Email: [rajkumar@example.com     ] │
│ Password: [**********            ] │
│                                     │
│ [ Sign In ]                         │
│                                     │
│ Don't have account? [Create one]    │
└─────────────────────────────────────┘

Step 4A: If No Account (First Time)
────────────────────────────────
Client clicks "Create account"

┌─────────────────────────────────────┐
│ Create Account to View Contract     │
│                                     │
│ Name:     [Raj Kumar             ] │
│ Email:    [rajkumar@example.com  ] │
│           (pre-filled from email)   │
│ Phone:    [+91-98765-43210       ] │
│ Password: [**********            ] │
│                                     │
│ [ Next ]                            │
└─────────────────────────────────────┘

Step 4B: ⚠️ CLIENT CONSENT SCREEN (DPDPA)
────────────────────────────────
┌─────────────────────────────────────┐
│ Data Processing Consent            │
│                                     │
│ Before you can view your contract: │
│                                     │
│ We will collect and process:       │
│                                     │
│ [✓] Your Personal Information      │
│     • Name, email, phone           │
│     Purpose: Account & contract    │
│              management            │
│     Retention: Until you delete    │
│     Required: YES                  │
│                                     │
│ [✓] Contract & Signature Data      │
│     • Your digital signature       │
│     • Aadhaar (if using eSign)    │
│     • IP address, device info      │
│     Purpose: Legal contract        │
│              execution             │
│     Retention: 7 years after       │
│                signing              │
│     Required: YES                  │
│                                     │
│ [ ] Marketing Communications       │
│     • Offers, updates from studio  │
│     Purpose: Keep you informed     │
│     Required: NO                   │
│                                     │
│ [View Privacy Policy]              │
│ [View Terms of Service]            │
│                                     │
│ Your Rights:                       │
│ • Access your data                 │
│ • Correct inaccurate data         │
│ • Delete your account             │
│ • Export your data                │
│ • Withdraw consent anytime        │
│                                     │
│ [✓] I agree to data processing     │
│                                     │
│ [ Continue to Contract ]           │
└─────────────────────────────────────┘

Step 5: View Contract
────────────────────────────────
After consent, client sees:

┌─────────────────────────────────────┐
│ Wedding Photography Agreement       │
│ Contract #: CONT-2024-1001         │
│ Status: Pending Signature          │
│                                     │
│ [Full contract content displayed]  │
│                                     │
│ [Read Contract ▼]                  │
│ [Sign Contract]                    │
└─────────────────────────────────────┘

Step 6: Sign Contract
────────────────────────────────
┌─────────────────────────────────────┐
│ Sign Contract                      │
│                                     │
│ Choose signing method:             │
│                                     │
│ Option 1: Draw Signature (Free)    │
│ [Draw your signature below]        │
│ ┌─────────────────────────────┐   │
│ │    [Canvas area]            │   │
│ └─────────────────────────────┘   │
│ [ Clear ]                          │
│                                     │
│ Option 2: Aadhaar eSign (₹10)      │
│ [Sign with Aadhaar]                │
│ (Government-verified, more secure) │
│                                     │
│ [✓] I have read and agree to      │
│     terms of this contract         │
│                                     │
│ [ Submit Signature ]               │
└─────────────────────────────────────┘

Step 7: Contract Signed ✅
────────────────────────────────
┌─────────────────────────────────────┐
│ ✅ Contract Signed Successfully!    │
│                                     │
│ Signed on: Nov 26, 2024, 2:30 PM  │
│ Method: Aadhaar eSign              │
│ Signature ID: SIG_abc123           │
│                                     │
│ 📧 Confirmation sent to your email │
│                                     │
│ [Download Signed Contract]         │
│ [View Contract]                    │
│ [Back to Dashboard]                │
└─────────────────────────────────────┘
```

---

## When Does Consent Screen Appear?

### Summary Table:

| User Type | When Consent Appears | What They Consent To |
|-----------|---------------------|---------------------|
| **Studio Owner** | When creating studio account | Processing client data on their behalf |
| **Client (First time)** | When accessing first contract/gallery | Their personal data being processed |
| **Client (Existing)** | Already consented, skip | - |

### Detailed Timing:

```
STUDIO OWNER:
├── Sign up for studio account
├── ⚠️ Consent screen appears HERE
├── Gives consent for business operations
└── Can now process client data

CLIENT (New):
├── Receives email: "View your contract"
├── Clicks link
├── No account yet
├── "Create account" or "Continue as guest"
├── ⚠️ Consent screen appears HERE
├── Gives consent for their data
└── Can now view/sign contract

CLIENT (Existing):
├── Already has account
├── Already gave consent
├── Logs in normally
├── ⚠️ No consent screen (already consented)
└── Can view/sign contract immediately
```

---

## Critical Understanding: Client Data Flow

### The Problem You're Asking About:

**Your question:** "Studio owner uploads client photos, so when do clients consent?"

**The answer:** There are TWO layers of consent!

### Layer 1: Studio's Consent (When Studio Signs Up)

```
Studio Owner's Consent Covers:
✅ "I am authorized to collect client data"
✅ "I will obtain necessary permissions from clients"
✅ "I agree to use Photo Proof to manage client data"

What this means:
- Studio owner takes responsibility
- Studio owner must have client permission separately
- Photo Proof trusts studio owner to handle client relationships
- Studio owner is "Data Fiduciary" for their clients
```

**Legal basis:**
- Studio owner has contractual relationship with clients
- Studio owner acts as "Data Fiduciary"
- Photo Proof acts as "Data Processor" for studio
- This is LEGAL under DPDPA

### Layer 2: Client's Consent (When Client Accesses Portal)

```
Client's Consent Covers:
✅ "I agree to Photo Proof processing my data"
✅ "I agree to use this platform for contracts"
✅ "I give permission to store my signature"

When collected:
- First time client clicks contract link
- First time client logs into client portal
- Before client signs any contract

What this means:
- Client explicitly agrees to use digital platform
- Client agrees to e-signature
- Legal protection for all parties
```

---

## Three Different Workflows

### Workflow A: Client With Account (Most Common)

```
Day 1: Studio creates client account
────────────────────────────────────
Studio Dashboard > Clients > Add New Client

Studio enters:
• Name: Raj Kumar
• Email: raj@example.com
• Phone: +91-9876543210

Client account created (no password yet)

Day 2: Studio uploads photos
────────────────────────────────────
Studio uploads wedding photos to Raj's gallery
(No client consent needed yet - photos not shared)

Day 5: Studio sends contract
────────────────────────────────────
Studio creates contract for Raj
Clicks "Send to Client"

Email sent to: raj@example.com

Day 5 (30 min later): Client receives email
────────────────────────────────────
📧 Subject: "Contract from Napster Photography"

Raj clicks [Review & Sign]

Day 5 (31 min later): First-time access
────────────────────────────────────
Link opens: https://photoproof.com/client/contract/abc123

┌─────────────────────────────────────┐
│ Set Your Password                  │
│                                     │
│ Hi Raj Kumar,                      │
│                                     │
│ Napster Photography has invited you│
│ to view your contract.             │
│                                     │
│ Create a password to continue:     │
│ Password: [**********            ] │
│ Confirm:  [**********            ] │
│                                     │
│ [ Next ]                            │
└─────────────────────────────────────┘

↓

⚠️ CONSENT SCREEN APPEARS HERE
┌─────────────────────────────────────┐
│ Data Processing Consent            │
│                                     │
│ To access your contract, we need   │
│ to process your personal data:     │
│                                     │
│ [✓] Contract Services (Required)   │
│     • View contracts from studios  │
│     • Sign contracts electronically│
│     • Download signed copies       │
│     • Receive notifications        │
│                                     │
│ Data we collect:                   │
│ • Your name, email, phone          │
│ • Your signature (when you sign)   │
│ • IP address, device info          │
│ • Aadhaar (only for Aadhaar eSign) │
│                                     │
│ Data provided by:                  │
│ • Napster Photography (your studio)│
│                                     │
│ Your rights:                       │
│ • Access your data                 │
│ • Correct errors                   │
│ • Delete account                   │
│ • Withdraw consent                 │
│                                     │
│ [View Privacy Policy]              │
│ [View Terms]                       │
│                                     │
│ [✓] I agree to data processing     │
│                                     │
│ [ Continue to Contract ]           │
└─────────────────────────────────────┘

↓

Contract page opens
Raj can now view and sign contract ✅
```

**Key Point:** Consent is collected **WHEN CLIENT FIRST ACCESSES the platform**, not when studio uploads photos!

---

### Workflow B: Client Without Account (Public Contract Link)

```
Day 1: Studio creates contract
────────────────────────────────────
Studio sends contract via email
NO client account needed

Day 1 (1 hour later): Client receives email
────────────────────────────────────
📧 Email to: raj@example.com

"You have received a contract.
 No account needed to view and sign."

[Review & Sign] ← Public link

Day 1 (1 hour 5 min): Client clicks
────────────────────────────────────
Link opens: https://photoproof.com/public/sign/xyz789

⚠️ CONSENT SCREEN APPEARS IMMEDIATELY
┌─────────────────────────────────────┐
│ Before Viewing Contract            │
│                                     │
│ This contract is from:             │
│ Napster Photography                │
│                                     │
│ To view and sign this contract,    │
│ we need to process:                │
│                                     │
│ [✓] Your signature data            │
│     • Digital signature image      │
│     • Timestamp, IP address        │
│     • Device information           │
│     Purpose: Legal contract        │
│              execution             │
│     Retention: 7 years             │
│                                     │
│ [✓] Aadhaar verification (optional)│
│     • Only if you choose Aadhaar   │
│       eSign method                 │
│     • Not stored permanently       │
│                                     │
│ Your rights:                       │
│ • Request copy of signed contract  │
│ • Verify your signature           │
│ • Contact us about your data      │
│                                     │
│ [View Privacy Policy]              │
│                                     │
│ [✓] I consent to data processing   │
│     for contract signing           │
│                                     │
│ [ Continue to Contract ]           │
└─────────────────────────────────────┘

↓

Contract page opens
Client can view full contract

↓

When ready to sign:
┌─────────────────────────────────────┐
│ Sign Contract                      │
│                                     │
│ Please provide your information:   │
│ Name:  [Raj Kumar              ]   │
│ Email: [raj@example.com        ]   │
│ Phone: [+91-98765-43210        ]   │
│                                     │
│ Choose signing method:             │
│ ( ) Draw Signature                 │
│ ( ) Aadhaar eSign                  │
│                                     │
│ [Next]                             │
└─────────────────────────────────────┘

↓

Signature screen
(Canvas or Aadhaar)

↓

Contract signed ✅
No account created (unless client wants one)
```

**Key Point:** Client consents **BEFORE viewing contract**, even without creating account!

---

### Workflow C: Client Portal Access

```
Day 1: Client wants to see all their contracts
────────────────────────────────────
Goes to: https://photoproof.com

Clicks: "Client Login"

If first time:
┌─────────────────────────────────────┐
│ Client Portal - Sign Up            │
│                                     │
│ Email: [raj@example.com         ]  │
│                                     │
│ [Continue]                         │
└─────────────────────────────────────┘

↓

⚠️ CONSENT SCREEN
(Same as Workflow B)

↓

Create password

↓

Dashboard opens
```

---

## Critical Question Answered: Photo Uploads

### Your Concern: "Studio uploads client photos - where's consent?"

**Answer: Multi-layer consent model**

#### Layer 1: Studio-Client Relationship (Offline)

**What happens in real world:**
```
1. Client books photography session
2. Client signs OFFLINE contract or agreement:
   "I authorize Napster Photography to:
   - Take my photographs
   - Process my photos
   - Share photos via online gallery
   - Use photos for contract documentation"
3. This is YOUR responsibility as photographer
```

**In your app:**
```
Studio Dashboard > Add Client

┌─────────────────────────────────────┐
│ Add New Client                     │
│                                     │
│ Client Name: [Raj Kumar         ]  │
│ Email:       [raj@example.com   ]  │
│ Phone:       [+91-9876543210    ]  │
│                                     │
│ [✓] I confirm I have obtained      │
│     necessary authorization from   │
│     this client to process their   │
│     personal data                  │
│                                     │
│ [ Add Client ]                     │
└─────────────────────────────────────┘
```

**This checkbox protects YOU by:**
- Creating record that you had permission
- Making you acknowledge your responsibility
- DPDPA compliance (you're acting as Data Fiduciary)

#### Layer 2: Client-Platform Relationship (Online)

**What happens when client accesses platform:**
```
Client clicks contract link
↓
⚠️ Platform consent screen appears
↓
Client consents to:
- Photo Proof processing their data
- Digital signature storage
- Using platform for contracts
```

**This protects:**
- Photo Proof (the platform)
- Creates direct relationship with client
- Legal compliance for platform

---

## The Complete Picture

### Data Flow & Consent Points

```
┌─────────────────────────────────────────────────────────────┐
│                    COMPLETE DATA FLOW                       │
└─────────────────────────────────────────────────────────────┘

Real World (Offline):
    Client books photography
         ↓
    📝 Client signs booking form/agreement
         ↓
    Client gives permission to photographer
         ↓
    ✅ CONSENT POINT 1: Offline consent to photographer

Photo Proof Platform:
    Photographer creates studio account
         ↓
    ⚠️ CONSENT POINT 2: Studio consents to use platform
         ↓
    ✅ Studio can now process client data via platform
         ↓
    Studio uploads client data (name, email, phone)
         ↓
    Studio uploads client photos
         ↓
    Studio creates contract
         ↓
    Studio sends contract to client

Client Portal:
    Client receives email
         ↓
    Client clicks link
         ↓
    ⚠️ CONSENT POINT 3: Client consents to platform
         ↓
    ✅ Client can now use platform
         ↓
    Client views contract
         ↓
    Client signs contract
         ↓
    Contract executed ✅

ALL THREE CONSENT POINTS REQUIRED FOR FULL COMPLIANCE!
```

---

## Practical Implementation

### Consent Timing - Exact Moments

**Moment 1: Studio Signup (You see this once)**
```
When: You create your studio account
Where: During studio registration
Who: You (the studio owner)
What: Consent to process client data
Shows: Once per studio account
```

**Moment 2: Client First Access (Client sees this once)**
```
When: Client first accesses ANY feature
Where: Before viewing contract, gallery, or anything
Who: Your client (e.g., Raj Kumar)
What: Consent to have their data processed by platform
Shows: Once per client, first access only
```

**Moment 3: Contract Signing (Every contract)**
```
When: Client is about to sign specific contract
Where: On signature page
Who: Client
What: Agreement to THIS specific contract's terms
Shows: Every time, for each contract
This is NOT DPDPA consent - this is contract agreement!
```

### Example Timeline:

```
January 1, 2025:
- You create studio account
- ⚠️ You see consent screen (DPDPA)
- ✅ You consent once
- Never see it again

January 15, 2025:
- You upload client "Raj Kumar" data
- You upload his wedding photos
- Client doesn't see anything yet (no access)

January 20, 2025:
- You send contract to Raj
- Raj clicks email link
- ⚠️ Raj sees consent screen (DPDPA) - FIRST TIME
- ✅ Raj consents
- Raj views contract
- Raj signs contract ✅

February 10, 2025:
- You send ANOTHER contract to Raj
- Raj clicks link
- ✅ No consent screen (already consented on Jan 20)
- Raj goes straight to contract
- Raj signs ✅

March 5, 2025:
- You send contract to NEW client "Priya"
- Priya clicks link
- ⚠️ Priya sees consent screen - HER FIRST TIME
- ✅ Priya consents
- Priya views and signs ✅
```

---

## Special Cases

### Case 1: Client Never Accesses Platform

```
Scenario:
- Studio uploads client photos
- Studio creates contract
- Studio prints contract
- Client signs on PAPER (offline)

DPDPA Impact:
- Studio already consented (when they signed up)
- Client never uses platform, so no platform consent needed
- Studio is responsible for client data (as Data Fiduciary)
- Platform is just Data Processor for studio

Compliance: ✅ OK
Reason: Client data processed under studio's consent
```

### Case 2: Guest Signing (No Account)

```
Scenario:
- Client receives contract link
- Clicks link
- Sees consent screen ⚠️
- Consents ✅
- Views contract
- Signs contract
- Leaves (never creates account)

DPDPA Impact:
- Client consented before any processing
- Signature data stored with consent record
- No account created, but consent still valid
- Can still exercise rights (via email to you)

Compliance: ✅ OK
Reason: Consent obtained before processing
```

### Case 3: Bulk Upload of Client Data

```
Scenario:
- Studio has 100 existing clients
- Studio uploads all at once via CSV

What happens:
┌─────────────────────────────────────┐
│ Bulk Import Clients                │
│                                     │
│ Upload CSV with client data        │
│                                     │
│ [✓] I confirm that:                │
│   • I have existing relationship   │
│     with all these clients         │
│   • I have their authorization to  │
│     process their data             │
│   • They have agreed to use my     │
│     photography services           │
│                                     │
│ [ Upload 100 Clients ]             │
└─────────────────────────────────────┘

Clients imported ✅

When each client first accesses platform:
- They see consent screen
- They provide their consent
- Platform consent added to studio consent

Compliance: ✅ OK
Reason: Studio authorized (Layer 1)
        + Client consent when accessing (Layer 2)
```

---

## Consent Matrix (Who Consents When)

| Action | Studio Consent | Client Consent | When Client Consents |
|--------|---------------|----------------|---------------------|
| Studio creates account | ✅ Required | N/A | - |
| Studio uploads client data | ✅ Covered by studio | Not yet | - |
| Studio creates contract | ✅ Covered by studio | Not yet | - |
| Studio SENDS contract | ✅ Covered by studio | Not yet | - |
| Client RECEIVES email | ✅ Covered by studio | Not yet | - |
| Client CLICKS link | ✅ Covered by studio | ⚠️ Required now | **First access to platform** |
| Client VIEWS contract | ✅ Yes | ✅ Must be given | Already obtained |
| Client SIGNS contract | ✅ Yes | ✅ Must be given | Already obtained |

---

## Your Workflow (Simplified)

### What YOU (Studio Owner) Do:

```
1. Create studio account (one time)
   → See consent screen
   → Agree to process client data
   → Never see consent screen again ✅

2. Add clients to your studio
   → Enter their basic info (name, email, phone)
   → Checkbox: "I have their authorization"
   → No consent screen for clients yet ✅

3. Upload client photos
   → Photos stored securely
   → Clients don't have access yet
   → No consent screen needed yet ✅

4. Create contract for client
   → Fill in contract details
   → Preview contract
   → Save as draft or send ✅

5. Send contract to client
   → Enter client email
   → Click "Send Contract"
   → Email sent with secure link
   → You're done! ✅
```

### What YOUR CLIENT Does:

```
1. Receives email notification
   → "You have a new contract"
   
2. Clicks "Review & Sign" link
   → Opens secure contract page
   
3. FIRST TIME ONLY: Sees consent screen ⚠️
   → Reads what data will be processed
   → Agrees to consent
   → Proceeds
   
4. Views full contract
   → Reads all terms
   → Scrolls to bottom
   
5. Clicks "Sign Contract"
   → Chooses: Draw signature or Aadhaar eSign
   → Signs
   → Done! ✅
   
6. NEXT TIME: No consent screen
   → Already consented on first access
   → Goes straight to contract
```

---

## Technical Implementation

### Backend: Track Consent Status

```python
# User model
class User:
    id: str
    email: str
    role: str  # "studio" or "client"
    
    # DPDPA consent tracking
    consent_given: bool = False
    consent_timestamp: datetime = None
    consent_ip_address: str = None
    consent_version: str = "1.0"  # If you update consent terms

# Check before showing content
def require_consent(user_id):
    user = db.query(User).get(user_id)
    
    if not user.consent_given:
        # Redirect to consent screen
        return redirect('/consent')
    
    # Consent already given, proceed
    return proceed_to_requested_page()
```

### Frontend: Consent Guard

```jsx
// App.tsx - Route guard
function AppContent() {
  const { user, loading } = useAuth();
  const [needsConsent, setNeedsConsent] = useState(false);
  
  useEffect(() => {
    if (user && !user.consent_given) {
      setNeedsConsent(true);
    }
  }, [user]);
  
  // Show consent screen if needed
  if (needsConsent) {
    return <ConsentScreen 
      onConsent={handleConsent} 
      userType={user.role}
    />;
  }
  
  // Normal app flow
  return <NormalApp />;
}

// Consent Screen Component
function ConsentScreen({ onConsent, userType }) {
  const [agreed, setAgreed] = useState(false);
  
  const handleSubmit = async () => {
    // Record consent
    await api.post('/v2/data-rights/consent', {
      consent_given: true,
      timestamp: new Date().toISOString(),
      consent_version: "1.0"
    });
    
    // Continue to app
    onConsent();
  };
  
  return (
    <div className="consent-screen">
      <h1>Data Processing Consent</h1>
      
      {userType === 'studio' ? (
        <StudioConsentContent />
      ) : (
        <ClientConsentContent />
      )}
      
      <Checkbox 
        checked={agreed}
        onChange={setAgreed}
      >
        I agree to data processing
      </Checkbox>
      
      <Button 
        disabled={!agreed}
        onClick={handleSubmit}
      >
        Continue
      </Button>
    </div>
  );
}
```

---

## Summary Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    CONSENT FLOW                         │
└─────────────────────────────────────────────────────────┘

STUDIO OWNER:
┌─────────┐     ┌────────────┐     ┌──────────────┐
│ Sign Up │ --> │ Consent    │ --> │ Use Platform │
│         │     │ Screen ⚠️  │     │ Upload data  │
└─────────┘     └────────────┘     └──────────────┘
                  (Shows ONCE)        (Forever after)

CLIENT (New):
┌─────────┐     ┌────────────┐     ┌──────────────┐
│ Click   │ --> │ Consent    │ --> │ View/Sign    │
│ Link    │     │ Screen ⚠️  │     │ Contract     │
└─────────┘     └────────────┘     └──────────────┘
                  (Shows ONCE)        (Forever after)

CLIENT (Existing):
┌─────────┐     ┌──────────────┐
│ Click   │ --> │ View/Sign    │
│ Link    │     │ Contract     │
└─────────┘     └──────────────┘
              (No consent - already given)
```

---

## Costs Summary (From Your Question)

### Development Costs

**Consent System:**
- Consent screen UI: ₹10,000-15,000
- Consent storage backend: ₹10,000-15,000
- Consent management page: ₹10,000-20,000
- **Total:** ₹30,000-50,000 ($360-600)

**Other DPDPA Features:**
- Data export: ₹30,000-50,000
- Account deletion: ₹40,000-60,000
- Privacy settings: ₹15,000-30,000
- Audit logging: ₹20,000-30,000
- **Total:** ₹1,35,000-1,70,000 ($1,620-2,040)

**Grand Total Development:** ₹1,65,000-2,20,000 ($1,980-2,640)

### Legal Costs

- Privacy Policy: ₹15,000-50,000
- Terms of Service: ₹20,000-60,000
- Legal consultation: ₹50,000-150,000
- **Total:** ₹85,000-2,60,000 ($1,020-3,120)

### Total Everything

**Minimum (bare basics):** ₹55,000-1,20,000 ($660-1,440)
**Complete (all features):** ₹2,50,000-4,80,000 ($3,000-5,760)
**With lawyer:** ₹3,35,000-7,40,000 ($4,020-8,880)

---

## Can You Skip Any of This?

### Absolute Must-Have (Can't skip):
- ✅ Consent screen (both studio and client)
- ✅ Privacy Policy (even basic template)
- ✅ Terms of Service
- ✅ Basic audit logging

**Cost:** ₹55,000-1,20,000  
**Penalty if skip:** Up to ₹250 crore fine

### Should-Have (Skip at your own risk):
- ⚠️ Data export
- ⚠️ Account deletion
- ⚠️ Data correction

**Cost:** ₹80,000-1,30,000  
**Penalty if skip:** Up to ₹200 crore fine + user complaints

### Nice-to-Have (Can add later):
- 🟢 Enhanced logging
- 🟢 Security audit
- 🟢 Breach response plan

**Cost:** ₹70,000-1,50,000  
**Penalty if skip:** ₹50 crore fine + reputation damage

---

## Final Answer to Your Question

**Q: "When does consent screen open? Studio uploads photos, how do we collect client signature?"**

**A:** 

**Consent screen opens:**
1. **For studio owner:** When YOU create studio account (one time)
2. **For client:** When client FIRST accesses platform (via contract link or login)

**How it works:**
1. You upload photos without client seeing consent (your authorization covers this)
2. You create contract
3. You send to client
4. Client clicks link
5. **⚠️ Consent screen appears for client** (their first time)
6. Client agrees
7. Client can now view and sign

**Key insight:** 
- Studio consent = Your authorization to process client data
- Client consent = Client's authorization for platform to process their data
- Both needed, but at different times!

**Think of it like a restaurant:**
- Restaurant owner (you) gets business license (studio consent)
- Customer (client) agrees to eat there when they enter (client consent)
- Owner doesn't need customer permission to buy ingredients
- But customer agrees to the meal when they order

Does this make sense now? 🤔
