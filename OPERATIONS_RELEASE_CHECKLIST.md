# Operations Release Checklist

## Latviesu

### 1. Production signing secrets
- Parbaudi, ka release keystore un paroles ir pieejamas tikai atbildigajiem.
- Pirms release palaides validē ievades (`keystore_base64`, `keystore_password`, `key_alias`, `key_password`).
- Dokumente pedejo atslēgu rotacijas datumu.

### 2. Real-device signed release validation (TC52)
- Uzinstalē signed release APK uz TC52.
- Izpildi minimālo scenāriju:
  - Skenē zināmu ierīci (jāielādē no DB)
  - Skenē nezināmu ierīci (jāparādās register plūsmai)
  - Saglabā jaunu ierīci
  - Pārbaudi offline queue un pēc tam sync
- Fiksē rezultātu ar build numuru un datumu.

### 3. Admin token process
- Definē, kurš izsniedz `device_admin` piekļuvi.
- Definē token derīguma termiņu un atjaunošanas procedūru.
- Definē atsaukšanas procedūru (incidenta gadījumā).

### 4. Backup and restore cadence
- Katru dienu: Supabase dump.
- Katru nedēļu: atjaunošanas drills test vidē.
- Reizi mēnesī: pārskats par pēdējiem backup/restore rezultātiem.

## English

### 1. Production signing secrets
- Ensure release keystore and passwords are accessible only to authorized operators.
- Validate required inputs before release run (`keystore_base64`, `keystore_password`, `key_alias`, `key_password`).
- Record last key rotation date.

### 2. Real-device signed release validation (TC52)
- Install signed release APK on TC52.
- Execute minimum scenario:
  - Scan known device (must load from DB)
  - Scan unknown device (must show register flow)
  - Save new device
  - Verify offline queue and then sync
- Record outcome with build number and date.

### 3. Admin token process
- Define who can issue `device_admin` access.
- Define token lifetime and refresh procedure.
- Define revocation procedure for incident response.

### 4. Backup and restore cadence
- Daily: Supabase dump.
- Weekly: restore drill in test environment.
- Monthly: review of latest backup/restore outcomes.
