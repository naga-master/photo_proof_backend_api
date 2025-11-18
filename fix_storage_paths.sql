-- Fix storage paths: Add /originals/ to all photos that don't have it yet
UPDATE photos 
SET storage_path = 
    SUBSTR(storage_path, 1, INSTR(storage_path, '/') + LENGTH(RTRIM(SUBSTR(storage_path, 1, INSTR(SUBSTR(storage_path, INSTR(storage_path, '/') + 1), '/') + INSTR(storage_path, '/')), '/')) - 1) || 
    '/originals/' || 
    SUBSTR(storage_path, INSTR(storage_path, '/') + LENGTH(RTRIM(SUBSTR(storage_path, 1, INSTR(SUBSTR(storage_path, INSTR(storage_path, '/') + 1), '/') + INSTR(storage_path, '/')), '/')) + 1)
WHERE storage_path LIKE 'projects/%' 
AND storage_path NOT LIKE '%/originals/%'
AND storage_path NOT LIKE '%/versions/%';

-- Show updated records
SELECT id, project_id, storage_path FROM photos WHERE id IN (797, 798, 799, 800, 801, 808, 809, 810, 811);
