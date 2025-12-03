# Multi-Tenant Deployment Checklist

This checklist ensures your multi-tenant system is properly configured and ready for production.

## Pre-Deployment Setup

### ✅ Phase 1: Database Setup

- [ ] **PostgreSQL Installed** (Optional but recommended)
  ```bash
  brew install postgresql@16
  brew services start postgresql@16
  ```

- [ ] **Database Created**
  ```bash
  createdb photo_proof_production
  ```

- [ ] **Database User Created**
  ```sql
  CREATE USER photo_proof_user WITH PASSWORD 'secure_password_here';
  GRANT ALL PRIVILEGES ON DATABASE photo_proof_production TO photo_proof_user;
  ```

- [ ] **DATABASE_URL Environment Variable Set**
  ```bash
  export DATABASE_URL="postgresql://photo_proof_user:password@localhost/photo_proof_production"
  # Or for SQLite:
  export DATABASE_URL="sqlite:///./photo_proof.db"
  ```

### ✅ Phase 2: Dependencies

- [ ] **Python Dependencies Installed**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **Verify psycopg2-binary installed** (for PostgreSQL)
  ```bash
  python -c "import psycopg2; print('✅ psycopg2 installed')"
  ```

### ✅ Phase 3: Database Initialization

- [ ] **Initialize Multi-Tenant Tables**
  ```bash
  python scripts/init_multi_tenant_db.py
  ```

- [ ] **Verify Tables Created**
  ```bash
  # For SQLite:
  sqlite3 photo_proof.db ".tables"
  
  # For PostgreSQL:
  psql $DATABASE_URL -c "\dt"
  ```

- [ ] **Verify Subscription Plans Seeded**
  ```bash
  # Check that 3 plans exist
  python -c "from app.db.session import SessionLocal; from app.db.models import SubscriptionPlan; db = SessionLocal(); print(f'Plans: {db.query(SubscriptionPlan).count()}'); db.close()"
  ```

### ✅ Phase 4: Local Testing Setup

- [ ] **Add Test Domains to /etc/hosts**
  ```bash
  sudo tee -a /etc/hosts << 'EOF'
  127.0.0.1 demo.photoapp.local
  127.0.0.1 alpha.photoapp.local
  127.0.0.1 beta.photoapp.local
  127.0.0.1 gamma.photoapp.local
  EOF
  ```

- [ ] **Run Multi-Tenant Tests**
  ```bash
  python scripts/test_multi_tenant.py
  ```

- [ ] **Verify All Tests Pass**
  - Test 1: Studio creation ✅
  - Test 2: Tenant detection ✅
  - Test 3: Data isolation ✅
  - Test 4: Storage isolation ✅
  - Test 5: Subscription plans ✅

## Functional Testing

### ✅ Phase 5: API Testing

- [ ] **Start the Server**
  ```bash
  python main.py
  ```

- [ ] **Test Health Endpoint**
  ```bash
  curl http://localhost:8000/api/health
  # Expected: {"status": "healthy"}
  ```

- [ ] **Test Tenant Detection**
  ```bash
  curl -v -H 'Host: demo.photoapp.local' http://localhost:8000/api/health
  # Check for X-Studio-ID header in response
  ```

- [ ] **Test Studio Theme Endpoint**
  ```bash
  curl -H 'Host: demo.photoapp.local' http://localhost:8000/api/studio/current
  # Expected: JSON with studio theme data
  ```

- [ ] **Test Multiple Studios**
  ```bash
  curl -H 'Host: alpha.photoapp.local' http://localhost:8000/api/studio/current
  curl -H 'Host: beta.photoapp.local' http://localhost:8000/api/studio/current
  curl -H 'Host: gamma.photoapp.local' http://localhost:8000/api/studio/current
  ```

- [ ] **Test Storage Stats Endpoint**
  ```bash
  curl -H 'Host: demo.photoapp.local' http://localhost:8000/api/studio/storage/stats
  ```

- [ ] **Test Subscription Plans Endpoint**
  ```bash
  curl http://localhost:8000/api/studio/plans
  # Should return 3 plans: starter, professional, enterprise
  ```

### ✅ Phase 6: Data Isolation Testing

- [ ] **Create Project for Studio Alpha**
  ```bash
  # First, get auth token for studio alpha user
  # Then create project and verify only visible to alpha
  ```

- [ ] **Verify Studio Beta Cannot See Alpha's Data**
  ```bash
  # Query projects with beta studio context
  # Should return empty or only beta's projects
  ```

- [ ] **Test Cross-Tenant API Access Prevention**
  ```bash
  # Try to access alpha's project with beta's credentials
  # Should return 403 Forbidden or 404 Not Found
  ```

### ✅ Phase 7: Storage Testing

- [ ] **Verify Tenant Storage Directories Created**
  ```bash
  ls -la uploads/studios/
  # Should see directories for each studio
  ```

- [ ] **Test Photo Upload**
  ```bash
  # Upload a photo for studio alpha
  # Verify it's saved to uploads/studios/{alpha-studio-id}/photos/
  ```

- [ ] **Test Storage Quota Check**
  ```python
  from app.services.storage_service import tenant_storage
  within_quota, used, max = tenant_storage.check_storage_quota("studio-id", 10)
  print(f"Within quota: {within_quota}, Used: {used / (1024**3):.2f} GB")
  ```

- [ ] **Test File Deletion Security**
  ```python
  # Try to delete file outside studio directory
  # Should return False and log security violation
  ```

### ✅ Phase 8: Performance Testing

- [ ] **Test Cache Performance**
  ```bash
  # First request (cache miss)
  time curl -H 'Host: demo.photoapp.local' http://localhost:8000/api/studio/current
  
  # Second request (cache hit - should be faster)
  time curl -H 'Host: demo.photoapp.local' http://localhost:8000/api/studio/current
  ```

- [ ] **Test Concurrent Requests**
  ```bash
  # Simulate 10 concurrent requests
  for i in {1..10}; do
    curl -H 'Host: demo.photoapp.local' http://localhost:8000/api/studio/current &
  done
  wait
  ```

- [ ] **Verify Connection Pooling** (PostgreSQL only)
  ```bash
  # Check PostgreSQL connection count
  psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname='photo_proof_production';"
  ```

## Security Verification

### ✅ Phase 9: Security Checks

- [ ] **Test SQL Injection Prevention**
  ```bash
  # Try injecting SQL in studio_id
  curl -H "Host: 1' OR '1'='1" http://localhost:8000/api/health
  # Should not break or expose data
  ```

- [ ] **Test Path Traversal Prevention**
  ```python
  from app.services.storage_service import tenant_storage
  # Try to delete file outside studio directory
  result = tenant_storage.delete_file("studio-id", "../../etc/passwd")
  # Should return False and log security violation
  ```

- [ ] **Test Cross-Tenant Authentication**
  ```bash
  # Get token for studio A
  # Try to access studio B's resources
  # Should fail with 403 or 404
  ```

- [ ] **Verify Password Hashing**
  ```python
  from app.services.auth_service import AuthService
  hashed = AuthService.hash_password("test123")
  print(f"Hashed: {hashed[:20]}...")  # Should be bcrypt hash
  ```

- [ ] **Test Rate Limiting** (if implemented)
  ```bash
  # Send 100 requests rapidly
  # Verify rate limiting kicks in
  ```

## Production Readiness

### ✅ Phase 10: Configuration Review

- [ ] **SECRET_KEY is Strong and Unique**
  ```bash
  # Check .env file
  # SECRET_KEY should be long random string, not default
  ```

- [ ] **Database Credentials are Secure**
  ```bash
  # Verify strong password
  # Not using default credentials
  ```

- [ ] **CORS Origins are Configured**
  ```bash
  # Check .env CORS_ORIGINS
  # Should include production domains
  ```

- [ ] **Upload Directory Permissions**
  ```bash
  ls -la uploads/
  # Should be writable by application user
  ```

- [ ] **Log Directory Exists**
  ```bash
  ls -la logs/
  mkdir -p logs  # Create if needed
  ```

### ✅ Phase 11: Monitoring Setup

- [ ] **Log Files Rotating Properly**
  ```bash
  # Check log configuration in app/core/logging_config.py
  # Verify max size and backup count
  ```

- [ ] **Error Tracking Configured**
  ```bash
  # Consider adding Sentry or similar
  # For production error monitoring
  ```

- [ ] **Health Check Endpoint Working**
  ```bash
  curl http://localhost:8000/api/health
  # Use for uptime monitoring
  ```

- [ ] **Storage Monitoring**
  ```python
  # Set up alerts for storage quota
  # Monitor disk space usage
  ```

### ✅ Phase 12: Backup Strategy

- [ ] **Database Backup Script**
  ```bash
  # For PostgreSQL:
  pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
  
  # For SQLite:
  cp photo_proof.db photo_proof.db.backup_$(date +%Y%m%d_%H%M%S)
  ```

- [ ] **Automated Daily Backups**
  ```bash
  # Add to crontab
  0 2 * * * /path/to/backup_script.sh
  ```

- [ ] **Upload Directory Backup**
  ```bash
  # Backup entire uploads directory
  tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
  ```

## Frontend Integration

### ✅ Phase 13: Frontend Testing

- [ ] **Create StudioThemeProvider Component**
  ```tsx
  // See MULTI_TENANT_IMPLEMENTATION.md for example
  ```

- [ ] **Wrap App with StudioThemeProvider**
  ```tsx
  <StudioThemeProvider>
    <App />
  </StudioThemeProvider>
  ```

- [ ] **Test Dynamic Branding**
  ```bash
  # Access via different domains
  # Verify logos/colors change
  ```

- [ ] **Test Custom CSS Loading**
  ```bash
  # Add custom CSS to studio
  # Verify it's applied to frontend
  ```

## Production Deployment

### ✅ Phase 14: Production Checklist

- [ ] **Environment Variables Set**
  - DATABASE_URL ✅
  - SECRET_KEY ✅
  - CORS_ORIGINS ✅
  - UPLOADS_DIR ✅

- [ ] **SSL Certificates Configured**
  ```bash
  # Use Let's Encrypt or Cloudflare
  # Enable HTTPS for all domains
  ```

- [ ] **Firewall Rules**
  ```bash
  # Only expose necessary ports (80, 443)
  # Block direct database access
  ```

- [ ] **Process Manager**
  ```bash
  # Use systemd, supervisor, or PM2
  # Auto-restart on failure
  ```

- [ ] **Reverse Proxy**
  ```bash
  # Nginx or Caddy
  # SSL termination
  # Static file serving
  ```

### ✅ Phase 15: Post-Deployment Verification

- [ ] **Smoke Test All Endpoints**
  ```bash
  # Run through all API endpoints
  # Verify expected responses
  ```

- [ ] **Monitor Error Logs**
  ```bash
  tail -f logs/photo_proof_api.log
  # Watch for errors in first hour
  ```

- [ ] **Check Performance Metrics**
  ```bash
  # Response times
  # Database query counts
  # Memory usage
  ```

- [ ] **Verify SSL Working**
  ```bash
  curl https://yourdomain.com/api/health
  # Should not show certificate errors
  ```

## Maintenance

### ✅ Phase 16: Ongoing Maintenance

- [ ] **Weekly Database Backups**
- [ ] **Monthly Security Updates**
  ```bash
  pip list --outdated
  pip install -U package_name
  ```

- [ ] **Monitor Storage Growth**
  ```python
  # Check storage usage per studio
  # Alert if approaching limits
  ```

- [ ] **Review Logs Weekly**
  ```bash
  grep ERROR logs/photo_proof_api.log
  ```

- [ ] **Cache Cleanup**
  ```python
  from app.services.cache_service import cache
  cache.cleanup_expired()
  ```

## Rollback Plan

### 🆘 Emergency Rollback

If issues occur in production:

1. **Stop the Application**
   ```bash
   # Stop the service
   systemctl stop photo_proof
   ```

2. **Restore Database Backup**
   ```bash
   # PostgreSQL
   psql $DATABASE_URL < backup_20250121_120000.sql
   
   # SQLite
   cp photo_proof.db.backup_20250121 photo_proof.db
   ```

3. **Restore Code Version**
   ```bash
   git checkout previous-stable-tag
   ```

4. **Restart Application**
   ```bash
   systemctl start photo_proof
   ```

## Success Criteria

✅ Your multi-tenant system is production-ready when:

- [ ] All automated tests pass
- [ ] 3+ studios can operate independently
- [ ] Data isolation is verified
- [ ] Storage is properly partitioned
- [ ] Cache improves performance
- [ ] Security checks pass
- [ ] Backups are automated
- [ ] Monitoring is in place
- [ ] Documentation is complete
- [ ] Team is trained

## Getting Help

If you encounter issues:

1. Check `MULTI_TENANT_IMPLEMENTATION.md` for detailed docs
2. Review `scripts/README.md` for script usage
3. Check logs: `tail -f logs/photo_proof_api.log`
4. Verify database state
5. Test with curl commands
6. Check GitHub issues or documentation

---

**Version:** 1.0  
**Last Updated:** 2025-11-21  
**Maintained by:** Development Team
