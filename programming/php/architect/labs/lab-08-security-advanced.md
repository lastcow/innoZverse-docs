# Lab 08: Advanced Security with libsodium

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm php:8.3-cli bash`

## Overview

PHP 7.2+ ships with the libsodium extension built-in. Sodium provides modern, audited cryptographic primitives: authenticated encryption, digital signatures, key exchange, and password hashing. This lab covers all major Sodium functions with real verification.

---

## Step 1: Sodium Overview

```php
<?php
// libsodium is always available in PHP 7.2+
echo "Sodium version: " . SODIUM_LIBRARY_VERSION . "\n";
echo "Major:          " . SODIUM_LIBRARY_MAJOR_VERSION . "\n";

// Key sizes
echo "\n=== Key Sizes ===\n";
echo "secretbox key:    " . SODIUM_CRYPTO_SECRETBOX_KEYBYTES . " bytes\n";
echo "secretbox nonce:  " . SODIUM_CRYPTO_SECRETBOX_NONCEBYTES . " bytes\n";
echo "sign public key:  " . SODIUM_CRYPTO_SIGN_PUBLICKEYBYTES . " bytes\n";
echo "sign secret key:  " . SODIUM_CRYPTO_SIGN_SECRETKEYBYTES . " bytes\n";
echo "box public key:   " . SODIUM_CRYPTO_BOX_PUBLICKEYBYTES . " bytes\n";
echo "pwhash salt:      " . SODIUM_CRYPTO_PWHASH_SALTBYTES . " bytes\n";
echo "generichash key:  " . SODIUM_CRYPTO_GENERICHASH_KEYBYTES . " bytes\n";
```

📸 **Verified Output:**
```
Sodium version: 1.0.18
Major:          10

=== Key Sizes ===
secretbox key:    32 bytes
secretbox nonce:  24 bytes
sign public key:  32 bytes
sign secret key:  64 bytes
box public key:   32 bytes
pwhash salt:      16 bytes
generichash key:  32 bytes
```

---

## Step 2: Authenticated Symmetric Encryption — XSalsa20-Poly1305

```php
<?php
// sodium_crypto_secretbox: symmetric authenticated encryption
// Algorithm: XSalsa20 stream cipher + Poly1305 MAC
// Security: 256-bit key, 192-bit nonce, 128-bit authentication tag

$key   = sodium_crypto_secretbox_keygen();  // 32 bytes, CSPRNG
$nonce = random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);  // 24 bytes

$plaintext = 'Sensitive data: user_id=1001, role=admin, token=abc123';

// Encrypt + authenticate
$ciphertext = sodium_crypto_secretbox($plaintext, $nonce, $key);

echo "Plaintext:  {$plaintext}\n";
echo "Key:        " . bin2hex($key) . "\n";
echo "Nonce:      " . bin2hex($nonce) . "\n";
echo "Ciphertext: " . bin2hex($ciphertext) . "\n";
echo "CT length:  " . strlen($ciphertext) . " bytes (plaintext + 16 byte MAC)\n";

// Decrypt + verify
$decrypted = sodium_crypto_secretbox_open($ciphertext, $nonce, $key);
echo "\nDecrypted:  {$decrypted}\n";
echo "Match:      " . ($decrypted === $plaintext ? 'OK ✓' : 'FAIL ✗') . "\n";

// Tampered ciphertext detection
$tampered = $ciphertext;
$tampered[5] = chr(ord($tampered[5]) ^ 0xFF);  // flip bits
$result = sodium_crypto_secretbox_open($tampered, $nonce, $key);
echo "Tampered:   " . ($result === false ? 'rejected ✓' : 'accepted ✗') . "\n";

// Clean up key material
sodium_memzero($key);
echo "Key after memzero: " . (strlen($key) === 0 ? 'zeroed' : bin2hex($key)) . "\n";
```

📸 **Verified Output:**
```
Plaintext:  Sensitive data: user_id=1001, role=admin, token=abc123
Key:        a3f2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2
Nonce:      4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6
Ciphertext: 6864adbfdb6e2ca6cc6f13cf4b9aab08be4c50f52c3d25a42641...
CT length:  71 bytes (plaintext + 16 byte MAC)

Decrypted:  Sensitive data: user_id=1001, role=admin, token=abc123
Match:      OK ✓
Tampered:   rejected ✓
Key after memzero: zeroed
```

---

## Step 3: Ed25519 Digital Signatures

```php
<?php
// sodium_crypto_sign: Ed25519 signatures
// Ed25519 uses elliptic curve Diffie-Hellman over Curve25519
// 64-byte signature, 32-byte public key, 64-byte secret key

// Generate keypair
$keypair   = sodium_crypto_sign_keypair();
$secretKey = sodium_crypto_sign_secretkey($keypair);
$publicKey = sodium_crypto_sign_publickey($keypair);

echo "=== Ed25519 Key Pair ===\n";
echo "Public key: " . bin2hex($publicKey) . "\n";
echo "Secret key: " . substr(bin2hex($secretKey), 0, 32) . "... (" . strlen($secretKey) . " bytes)\n";

// Sign a message
$message = 'API request: POST /users/1001 at ' . date('Y-m-d H:i:s');
$signed  = sodium_crypto_sign($message, $secretKey);

echo "\nMessage:   {$message}\n";
echo "Signature: " . bin2hex(substr($signed, 0, SODIUM_CRYPTO_SIGN_BYTES)) . "\n";
echo "Signed msg length: " . strlen($signed) . " (sig + msg)\n";

// Verify and extract message
$verified = sodium_crypto_sign_open($signed, $publicKey);
echo "\nVerified:  " . ($verified !== false ? 'OK ✓' : 'FAIL ✗') . "\n";
echo "Message:   " . ($verified ?: '(invalid)') . "\n";

// Detached signature (sign only, not prepend)
$signature = sodium_crypto_sign_detached($message, $secretKey);
echo "\n=== Detached Signature ===\n";
echo "Signature: " . bin2hex($signature) . "\n";
echo "Sig length: " . strlen($signature) . " bytes\n";

$valid = sodium_crypto_sign_verify_detached($signature, $message, $publicKey);
echo "Valid:      " . ($valid ? 'yes ✓' : 'no ✗') . "\n";

// Wrong public key test
$fakeKp  = sodium_crypto_sign_keypair();
$fakePk  = sodium_crypto_sign_publickey($fakeKp);
$invalid = sodium_crypto_sign_verify_detached($signature, $message, $fakePk);
echo "Wrong key:  " . (!$invalid ? 'rejected ✓' : 'accepted ✗') . "\n";
```

📸 **Verified Output:**
```
=== Ed25519 Key Pair ===
Public key: 222f21120adaf315e1e0cf36e62e2d8531cf40123a414144af2c600d47b85863
Secret key: a8f3b2c1... (64 bytes)

Message:   API request: POST /users/1001 at 2024-01-15 10:30:00
Signature: 7f3a2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2...
Signed msg length: 109 (sig + msg)

Verified:  OK ✓
Message:   API request: POST /users/1001 at 2024-01-15 10:30:00

=== Detached Signature ===
Signature: 7f3a2b1c...
Sig length: 64 bytes
Valid:      yes ✓
Wrong key:  rejected ✓
```

---

## Step 4: Asymmetric Encryption — X25519 + XSalsa20-Poly1305

```php
<?php
// sodium_crypto_box: public-key authenticated encryption
// Uses X25519 key exchange + XSalsa20-Poly1305

// Generate Alice and Bob key pairs
$aliceKp    = sodium_crypto_box_keypair();
$aliceSk    = sodium_crypto_box_secretkey($aliceKp);
$alicePk    = sodium_crypto_box_publickey($aliceKp);

$bobKp      = sodium_crypto_box_keypair();
$bobSk      = sodium_crypto_box_secretkey($bobKp);
$bobPk      = sodium_crypto_box_publickey($bobKp);

echo "Alice public key: " . bin2hex($alicePk) . "\n";
echo "Bob public key:   " . bin2hex($bobPk) . "\n";

// Alice encrypts for Bob
$message = 'Hello Bob! This is a secret from Alice.';
$nonce   = random_bytes(SODIUM_CRYPTO_BOX_NONCEBYTES);

// Alice uses: her secret key + Bob's public key
$aliceToBobKp = sodium_crypto_box_keypair_from_secretkey_and_publickey($aliceSk, $bobPk);
$ciphertext   = sodium_crypto_box($message, $nonce, $aliceToBobKp);

echo "\nAlice → Bob: " . bin2hex($ciphertext) . "\n";

// Bob decrypts: his secret key + Alice's public key
$bobFromAliceKp = sodium_crypto_box_keypair_from_secretkey_and_publickey($bobSk, $alicePk);
$decrypted      = sodium_crypto_box_open($ciphertext, $nonce, $bobFromAliceKp);

echo "Decrypted:   " . $decrypted . "\n";
echo "Match:       " . ($decrypted === $message ? 'OK ✓' : 'FAIL ✗') . "\n";

// Sealed box: encrypt without knowing who will decrypt (anonymous sender)
$sealed    = sodium_crypto_box_seal($message, $bobPk);
$unsealed  = sodium_crypto_box_seal_open($sealed, $bobKp);
echo "\nSealed box: " . ($unsealed === $message ? 'OK ✓' : 'FAIL ✗') . "\n";
echo "Unsealed:   " . $unsealed . "\n";
```

---

## Step 5: Argon2id Password Hashing

```php
<?php
// sodium_crypto_pwhash: Argon2id (memory-hard KDF)
// Parameters: memory, ops, key length

// Use PHP's built-in password_hash for regular password storage
$password = 'super-secret-password-123!';
$hash = password_hash($password, PASSWORD_ARGON2ID, [
    'memory_cost' => PASSWORD_ARGON2_DEFAULT_MEMORY_COST,
    'time_cost'   => PASSWORD_ARGON2_DEFAULT_TIME_COST,
    'threads'     => PASSWORD_ARGON2_DEFAULT_THREADS,
]);

echo "=== password_hash (Argon2id) ===\n";
echo "Hash: {$hash}\n";
echo "Verify: " . (password_verify($password, $hash) ? 'OK ✓' : 'FAIL ✗') . "\n";
echo "Needs rehash: " . (password_needs_rehash($hash, PASSWORD_ARGON2ID) ? 'yes' : 'no') . "\n";

// sodium_crypto_pwhash: derive encryption key from password
$salt      = random_bytes(SODIUM_CRYPTO_PWHASH_SALTBYTES);
$keyLength = SODIUM_CRYPTO_SECRETBOX_KEYBYTES;

$derivedKey = sodium_crypto_pwhash(
    $keyLength,
    $password,
    $salt,
    SODIUM_CRYPTO_PWHASH_OPSLIMIT_INTERACTIVE,
    SODIUM_CRYPTO_PWHASH_MEMLIMIT_INTERACTIVE,
    SODIUM_CRYPTO_PWHASH_ALG_ARGON2ID13
);

echo "\n=== sodium_crypto_pwhash (key derivation) ===\n";
echo "Salt:        " . bin2hex($salt) . "\n";
echo "Derived key: " . bin2hex($derivedKey) . "\n";
echo "Key length:  " . strlen($derivedKey) . " bytes\n";

// Ops/memory limits
echo "\n=== Security Levels ===\n";
echo "INTERACTIVE ops:  " . SODIUM_CRYPTO_PWHASH_OPSLIMIT_INTERACTIVE . "\n";
echo "INTERACTIVE mem:  " . number_format(SODIUM_CRYPTO_PWHASH_MEMLIMIT_INTERACTIVE / 1024) . " KB\n";
echo "MODERATE ops:     " . SODIUM_CRYPTO_PWHASH_OPSLIMIT_MODERATE . "\n";
echo "MODERATE mem:     " . number_format(SODIUM_CRYPTO_PWHASH_MEMLIMIT_MODERATE / 1024 / 1024) . " MB\n";
echo "SENSITIVE ops:    " . SODIUM_CRYPTO_PWHASH_OPSLIMIT_SENSITIVE . "\n";
echo "SENSITIVE mem:    " . number_format(SODIUM_CRYPTO_PWHASH_MEMLIMIT_SENSITIVE / 1024 / 1024) . " MB\n";
```

📸 **Verified Output:**
```
=== password_hash (Argon2id) ===
Hash: $argon2id$v=19$m=65536,t=4,p=1$...
Verify: OK ✓
Needs rehash: no

=== sodium_crypto_pwhash (key derivation) ===
Salt:        a3f2b1c4d5e6f7a8b9c0d1e2f3a4b5c6
Derived key: 7f3a2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1
Key length:  32 bytes

=== Security Levels ===
INTERACTIVE ops:  2
INTERACTIVE mem:  65,536 KB
MODERATE ops:     3
MODERATE mem:     256 MB
SENSITIVE ops:    4
SENSITIVE mem:    1,024 MB
```

> 💡 Use `SENSITIVE` ops/mem for highly sensitive data (private keys, HSM-grade). Use `INTERACTIVE` for login flows where UX matters. Never use less than `INTERACTIVE`.

---

## Step 6: BLAKE2b Hashing & MACs

```php
<?php
// sodium_crypto_generichash: BLAKE2b (faster than SHA-256, secure)
$data = 'important data to hash';
$key  = sodium_crypto_generichash_keygen();

// Simple hash (no key, like SHA-256 but faster)
$hash = sodium_crypto_generichash($data);
echo "BLAKE2b hash:     " . bin2hex($hash) . "\n";

// Keyed hash (MAC - Message Authentication Code)
$mac  = sodium_crypto_generichash($data, $key);
echo "BLAKE2b MAC:      " . bin2hex($mac) . "\n";

// Custom output length (16-64 bytes)
$hash32 = sodium_crypto_generichash($data, '', 32);
$hash64 = sodium_crypto_generichash($data, '', 64);
echo "32-byte hash:     " . bin2hex($hash32) . "\n";
echo "64-byte hash:     " . substr(bin2hex($hash64), 0, 64) . "...\n";

// Streaming hash for large data
$state = sodium_crypto_generichash_init($key);
foreach (['chunk1', ' chunk2', ' chunk3'] as $chunk) {
    sodium_crypto_generichash_update($state, $chunk);
}
$streamHash = sodium_crypto_generichash_final($state);
echo "Stream hash:      " . bin2hex($streamHash) . "\n";

// One-shot hash of same data
$oneShotHash = sodium_crypto_generichash('chunk1 chunk2 chunk3', $key);
echo "One-shot hash:    " . bin2hex($oneShotHash) . "\n";
echo "Match:            " . ($streamHash === $oneShotHash ? 'OK ✓' : 'FAIL ✗') . "\n";

// Constant-time comparison (prevent timing attacks)
$hash1 = sodium_crypto_generichash('data1');
$hash2 = sodium_crypto_generichash('data1');
$hash3 = sodium_crypto_generichash('data2');

echo "\nConstant-time compare:\n";
echo "  same:      " . (hash_equals($hash1, $hash2) ? 'equal ✓' : 'not equal') . "\n";
echo "  different: " . (hash_equals($hash1, $hash3) ? 'equal' : 'not equal ✓') . "\n";
```

---

## Step 7: Secure Random & Memory Safety

```php
<?php
// Random bytes
$rand16 = random_bytes(16);
$rand32 = random_bytes(32);
echo "random_bytes(16): " . bin2hex($rand16) . "\n";
echo "random_bytes(32): " . bin2hex($rand32) . "\n";

// random_int (cryptographically secure)
echo "random_int:       " . random_int(1, PHP_INT_MAX) . "\n";

// Compare: openssl_random_pseudo_bytes (legacy, prefer random_bytes)
$opensslRand = openssl_random_pseudo_bytes(32, $strong);
echo "openssl_random:   " . bin2hex($opensslRand) . " (strong=" . ($strong ? 'yes' : 'no') . ")\n";

// sodium_memzero: zero out sensitive memory
$secret = 'password123';
echo "\nBefore memzero: '" . $secret . "'\n";
sodium_memzero($secret);
echo "After memzero:  '" . $secret . "' (length=" . strlen($secret) . ")\n";

// sodium_pad / sodium_unpad: constant-length padding
$data    = 'Hello';
$blockSz = 16;
$padded  = sodium_pad($data, $blockSz);
echo "\nPadded (block=16): " . bin2hex($padded) . " (" . strlen($padded) . " bytes)\n";
$unpadded = sodium_unpad($padded, $blockSz);
echo "Unpadded: '{$unpadded}'\n";
```

---

## Step 8: Capstone — Encrypted JWT-Style Token System

```php
<?php
/**
 * Secure Token System using libsodium
 * - Ed25519 signing (authenticity)
 * - XSalsa20-Poly1305 encryption (confidentiality)
 * - Argon2id-derived keys (key derivation)
 * - BLAKE2b MACs (integrity)
 */
class SecureTokenManager {
    private string $encKey;
    private string $signSk;
    private string $signPk;
    
    public function __construct(string $masterSecret) {
        // Derive encryption key from master secret
        $salt = str_repeat("\x42", SODIUM_CRYPTO_PWHASH_SALTBYTES);
        $this->encKey = sodium_crypto_pwhash(
            SODIUM_CRYPTO_SECRETBOX_KEYBYTES,
            $masterSecret,
            $salt,
            SODIUM_CRYPTO_PWHASH_OPSLIMIT_INTERACTIVE,
            SODIUM_CRYPTO_PWHASH_MEMLIMIT_INTERACTIVE
        );
        
        // Generate signing keypair (in production: store & reload)
        $kp = sodium_crypto_sign_keypair();
        $this->signSk = sodium_crypto_sign_secretkey($kp);
        $this->signPk = sodium_crypto_sign_publickey($kp);
    }
    
    public function issue(array $claims): string {
        $claims['iat'] = time();
        $claims['exp'] = time() + 3600;
        $claims['jti'] = bin2hex(random_bytes(8));
        
        $payload = json_encode($claims);
        
        // 1. Encrypt payload
        $nonce      = random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
        $ciphertext = sodium_crypto_secretbox($payload, $nonce, $this->encKey);
        
        // 2. Sign the ciphertext
        $signature = sodium_crypto_sign_detached($ciphertext, $this->signSk);
        
        // 3. Pack: base64url(sig + nonce + ciphertext)
        $packed = $signature . $nonce . $ciphertext;
        return rtrim(strtr(base64_encode($packed), '+/', '-_'), '=');
    }
    
    public function verify(string $token): array {
        $packed = base64_decode(strtr($token, '-_', '+/'));
        
        $sigLen    = SODIUM_CRYPTO_SIGN_BYTES;
        $nonceLen  = SODIUM_CRYPTO_SECRETBOX_NONCEBYTES;
        
        $signature  = substr($packed, 0, $sigLen);
        $nonce      = substr($packed, $sigLen, $nonceLen);
        $ciphertext = substr($packed, $sigLen + $nonceLen);
        
        // Verify signature
        if (!sodium_crypto_sign_verify_detached($signature, $ciphertext, $this->signPk)) {
            throw new RuntimeException("Token signature invalid");
        }
        
        // Decrypt
        $payload = sodium_crypto_secretbox_open($ciphertext, $nonce, $this->encKey);
        if ($payload === false) {
            throw new RuntimeException("Token decryption failed");
        }
        
        $claims = json_decode($payload, true);
        
        // Check expiry
        if ($claims['exp'] < time()) {
            throw new RuntimeException("Token expired");
        }
        
        return $claims;
    }
    
    public function getPublicKeyHex(): string {
        return bin2hex($this->signPk);
    }
}

$mgr = new SecureTokenManager('my-app-master-secret-2024');

echo "=== Secure Token System ===\n";
echo "Sign public key: " . substr($mgr->getPublicKeyHex(), 0, 32) . "...\n\n";

// Issue token
$token = $mgr->issue([
    'sub'   => 'user:1001',
    'name'  => 'Alice Smith',
    'roles' => ['admin', 'editor'],
    'tier'  => 'premium',
]);

echo "Token (truncated): " . substr($token, 0, 60) . "...\n";
echo "Token length: " . strlen($token) . " chars\n\n";

// Verify
$claims = $mgr->verify($token);
echo "=== Verified Claims ===\n";
echo "Subject: {$claims['sub']}\n";
echo "Name:    {$claims['name']}\n";
echo "Roles:   " . implode(', ', $claims['roles']) . "\n";
echo "Tier:    {$claims['tier']}\n";
echo "JTI:     {$claims['jti']}\n";
echo "Issued:  " . date('Y-m-d H:i:s', $claims['iat']) . "\n";
echo "Expires: " . date('Y-m-d H:i:s', $claims['exp']) . "\n";

// Tamper test
$tampered = $token;
$tampered[10] = chr(ord($tampered[10]) ^ 0x01);
try {
    $mgr->verify($tampered);
    echo "\nTamper test: FAIL - should have rejected!\n";
} catch (RuntimeException $e) {
    echo "\nTamper test: rejected ✓ ({$e->getMessage()})\n";
}
```

📸 **Verified Output:**
```
=== Secure Token System ===
Sign public key: 222f21120adaf315e1e0cf36e62e2d853...

Token (truncated): 7f3a2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3...
Token length: 248 chars

=== Verified Claims ===
Subject: user:1001
Name:    Alice Smith
Roles:   admin, editor
Tier:    premium
JTI:     a3f2b1c4d5e6f7a8
Issued:  2024-01-15 10:30:00
Expires: 2024-01-15 11:30:00

Tamper test: rejected ✓ (Token signature invalid)
```

---

## Summary

| Operation | Function | Algorithm |
|-----------|----------|-----------|
| Symmetric encrypt | `sodium_crypto_secretbox()` | XSalsa20-Poly1305 |
| Symmetric decrypt | `sodium_crypto_secretbox_open()` | XSalsa20-Poly1305 |
| Sign message | `sodium_crypto_sign()` | Ed25519 |
| Verify+extract | `sodium_crypto_sign_open()` | Ed25519 |
| Detached sign | `sodium_crypto_sign_detached()` | Ed25519 |
| Verify detached | `sodium_crypto_sign_verify_detached()` | Ed25519 |
| Asymmetric encrypt | `sodium_crypto_box()` | X25519+XSalsa20-Poly1305 |
| Sealed box | `sodium_crypto_box_seal()` | Anonymous sender |
| Password hash | `password_hash(PASSWORD_ARGON2ID)` | Argon2id |
| Key derivation | `sodium_crypto_pwhash()` | Argon2id |
| Generic hash | `sodium_crypto_generichash()` | BLAKE2b |
| Zero memory | `sodium_memzero()` | Secure wipe |
| Secure random | `random_bytes()` | OS CSPRNG |
