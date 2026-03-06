# Lab 08: JCA/JCE — Java Cryptography Architecture

**Time:** 60 minutes | **Level:** Architect | **Docker:** `docker run -it --rm zchencow/innozverse-java:latest bash`

---

## Overview

The Java Cryptography Architecture (JCA) and Extension (JCE) provide a provider-based cryptography framework. Master EC P-256 key generation, ECDSA signatures, ECDH key agreement, PBKDF2 key derivation, AES-GCM encryption, and KeyStore management.

---

## Step 1: JCA Provider Architecture

```
JCA Provider Model:
  Application
      │
  Security.getProvider("SunEC") / "SunJCE" / "SunJSSE"
      │
  ┌───▼──────────────────────────────────────────┐
  │  Provider (SunEC, Bouncy Castle, PKCS#11...) │
  │  - KeyPairGenerator("EC")                     │
  │  - Signature("SHA256withECDSA")               │
  │  - KeyAgreement("ECDH")                       │
  │  - Cipher("AES/GCM/NoPadding")               │
  │  - SecretKeyFactory("PBKDF2WithHmacSHA256")   │
  └──────────────────────────────────────────────┘
```

```java
import java.security.*;

public class ProviderList {
    public static void main(String[] args) {
        for (Provider p : Security.getProviders()) {
            System.out.println(p.getName() + " v" + p.getVersionStr());
        }
        System.out.println("\nEC algorithms available: " +
            Security.getAlgorithms("KeyPairGenerator").contains("EC"));
    }
}
```

---

## Step 2: EC P-256 Key Pair Generation

```java
import java.security.*;
import java.security.spec.*;
import java.util.Base64;

public class ECKeyGenDemo {
    public static void main(String[] args) throws Exception {
        // secp256r1 = P-256 = NIST P-256 = prime256v1 (same curve, different names)
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        KeyPair keyPair = kpg.generateKeyPair();
        
        PublicKey pub = keyPair.getPublic();
        PrivateKey priv = keyPair.getPrivate();
        
        System.out.println("Algorithm: " + pub.getAlgorithm());
        System.out.println("Format:    " + pub.getFormat()); // X.509
        System.out.println("Public key (X.509 DER, base64): ");
        System.out.println("  " + Base64.getEncoder().encodeToString(pub.getEncoded()));
        
        // Reconstruct from bytes
        KeyFactory kf = KeyFactory.getInstance("EC");
        PublicKey reconstructed = kf.generatePublic(new X509EncodedKeySpec(pub.getEncoded()));
        System.out.println("Reconstructed key equals: " + pub.equals(reconstructed));
    }
}
```

---

## Step 3: ECDSA Signatures

```java
import java.security.*;
import java.security.spec.*;
import java.util.Base64;

public class ECDSADemo {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        KeyPair kp = kpg.generateKeyPair();
        
        byte[] message = "Architect-level Java security".getBytes();
        
        // Sign
        Signature signer = Signature.getInstance("SHA256withECDSA");
        signer.initSign(kp.getPrivate(), new SecureRandom());
        signer.update(message);
        byte[] signature = signer.sign();
        
        System.out.println("Signature algorithm: SHA256withECDSA");
        System.out.println("Signature (DER): " + Base64.getEncoder().encodeToString(signature));
        System.out.println("Signature length: " + signature.length + " bytes (DER-encoded)");
        
        // Verify
        Signature verifier = Signature.getInstance("SHA256withECDSA");
        verifier.initVerify(kp.getPublic());
        verifier.update(message);
        boolean valid = verifier.verify(signature);
        System.out.println("Signature valid: " + valid);
        
        // Tampered message
        byte[] tampered = "Tampered message".getBytes();
        verifier.initVerify(kp.getPublic());
        verifier.update(tampered);
        System.out.println("Tampered valid:  " + verifier.verify(signature));
    }
}
```

> 💡 ECDSA signatures are **non-deterministic** by default (random k). For deterministic ECDSA use RFC 6979 (available in Bouncy Castle).

---

## Step 4: ECDH Key Agreement

```java
import java.security.*;
import java.security.spec.*;
import javax.crypto.*;
import java.util.Base64;

public class ECDHDemo {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        
        // Alice and Bob each generate their own key pair
        KeyPair aliceKP = kpg.generateKeyPair();
        KeyPair bobKP = kpg.generateKeyPair();
        
        // Alice computes shared secret using Bob's public key
        KeyAgreement aliceKA = KeyAgreement.getInstance("ECDH");
        aliceKA.init(aliceKP.getPrivate());
        aliceKA.doPhase(bobKP.getPublic(), true);
        byte[] aliceSecret = aliceKA.generateSecret();
        
        // Bob computes shared secret using Alice's public key
        KeyAgreement bobKA = KeyAgreement.getInstance("ECDH");
        bobKA.init(bobKP.getPrivate());
        bobKA.doPhase(aliceKP.getPublic(), true);
        byte[] bobSecret = bobKA.generateSecret();
        
        System.out.println("Alice secret: " + Base64.getEncoder().encodeToString(aliceSecret));
        System.out.println("Bob secret:   " + Base64.getEncoder().encodeToString(bobSecret));
        System.out.println("Secrets match: " + java.util.Arrays.equals(aliceSecret, bobSecret));
        System.out.println("(Use HKDF to derive AES key from shared secret)");
    }
}
```

---

## Step 5: PBKDF2 Key Derivation

```java
import java.security.spec.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import java.util.Base64;

public class PBKDF2Demo {
    public static void main(String[] args) throws Exception {
        // OWASP 2023 recommendation: 600,000 iterations for PBKDF2-SHA256
        String password = "correct-horse-battery-staple";
        byte[] salt = new SecureRandom().engineGenerateSeed(16); // 16 random bytes
        int iterations = 600_000;
        int keyLength = 256; // bits
        
        SecretKeyFactory skf = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        PBEKeySpec spec = new PBEKeySpec(
            password.toCharArray(),
            salt,
            iterations,
            keyLength
        );
        
        long start = System.currentTimeMillis();
        byte[] derivedKey = skf.generateSecret(spec).getEncoded();
        long elapsed = System.currentTimeMillis() - start;
        
        spec.clearPassword(); // zero the password from memory
        
        System.out.println("PBKDF2WithHmacSHA256");
        System.out.println("Iterations: " + iterations);
        System.out.println("Derived key: " + Base64.getEncoder().encodeToString(derivedKey));
        System.out.println("Time: " + elapsed + "ms");
        System.out.println("Key length: " + derivedKey.length + " bytes");
    }
}
```

> 💡 Store: `Base64(salt) + ":" + iterations + ":" + Base64(derivedKey)`. Never store just the hash — always include salt and iteration count.

---

## Step 6: AES-GCM Authenticated Encryption

```java
import java.security.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import java.util.Base64;

public class AESGCMDemo {
    static final int GCM_IV_LENGTH = 12;  // 96 bits — GCM standard
    static final int GCM_TAG_LENGTH = 128; // 128-bit authentication tag
    
    public static void main(String[] args) throws Exception {
        // Generate AES-256 key
        KeyGenerator kg = KeyGenerator.getInstance("AES");
        kg.init(256);
        SecretKey key = kg.generateKey();
        
        // Generate random IV (NEVER reuse an IV with the same key!)
        byte[] iv = new byte[GCM_IV_LENGTH];
        new SecureRandom().nextBytes(iv);
        GCMParameterSpec gcmSpec = new GCMParameterSpec(GCM_TAG_LENGTH, iv);
        
        // Encrypt
        byte[] plaintext = "Sensitive financial data: $1,000,000".getBytes();
        byte[] aad = "user-id:12345".getBytes(); // Additional Authenticated Data
        
        Cipher encCipher = Cipher.getInstance("AES/GCM/NoPadding");
        encCipher.init(Cipher.ENCRYPT_MODE, key, gcmSpec);
        encCipher.updateAAD(aad); // AAD is authenticated but not encrypted
        byte[] ciphertext = encCipher.doFinal(plaintext);
        
        System.out.println("IV (base64): " + Base64.getEncoder().encodeToString(iv));
        System.out.println("Ciphertext:  " + Base64.getEncoder().encodeToString(ciphertext));
        System.out.println("(ciphertext includes 16-byte GCM tag appended)");
        
        // Decrypt + verify authentication tag
        Cipher decCipher = Cipher.getInstance("AES/GCM/NoPadding");
        decCipher.init(Cipher.DECRYPT_MODE, key, gcmSpec);
        decCipher.updateAAD(aad);
        byte[] decrypted = decCipher.doFinal(ciphertext);
        System.out.println("Decrypted:   " + new String(decrypted));
        
        // Tampered ciphertext → AEADBadTagException
        try {
            ciphertext[0] ^= 1; // flip a bit
            Cipher badCipher = Cipher.getInstance("AES/GCM/NoPadding");
            badCipher.init(Cipher.DECRYPT_MODE, key, gcmSpec);
            badCipher.updateAAD(aad);
            badCipher.doFinal(ciphertext);
        } catch (AEADBadTagException e) {
            System.out.println("Tampered: AEADBadTagException (authentication failed)");
        }
    }
}
```

---

## Step 7: KeyStore — PKCS#12

```java
import java.security.*;
import java.security.cert.*;
import java.security.spec.*;
import javax.crypto.*;
import java.io.*;
import java.util.Base64;

public class KeyStoreDemo {
    public static void main(String[] args) throws Exception {
        // Generate EC key pair for keystore demo
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        KeyPair kp = kpg.generateKeyPair();
        
        // Create a PKCS#12 keystore
        KeyStore ks = KeyStore.getInstance("PKCS12");
        ks.load(null, null); // initialize empty
        
        // KeyStore entries: PrivateKeyEntry requires a certificate chain
        // (In production, use a self-signed cert or CA-issued cert)
        // For this demo, show the API patterns:
        System.out.println("KeyStore type: " + ks.getType());
        System.out.println("KeyStore provider: " + ks.getProvider().getName());
        System.out.println("Initial entry count: " + ks.size());
        
        // Store a SecretKey entry
        KeyGenerator kg = KeyGenerator.getInstance("AES");
        kg.init(256);
        SecretKey aesKey = kg.generateKey();
        
        KeyStore.SecretKeyEntry secretEntry = new KeyStore.SecretKeyEntry(aesKey);
        KeyStore.ProtectionParameter protection = new KeyStore.PasswordProtection("ks-password".toCharArray());
        ks.setEntry("aes-key-alias", secretEntry, protection);
        
        System.out.println("After storing SecretKey: " + ks.size() + " entries");
        System.out.println("Contains 'aes-key-alias': " + ks.containsAlias("aes-key-alias"));
        
        // Save to bytes
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ks.store(baos, "store-password".toCharArray());
        byte[] ksBytes = baos.toByteArray();
        System.out.println("KeyStore serialized: " + ksBytes.length + " bytes (PKCS#12)");
        
        // Load from bytes
        KeyStore loaded = KeyStore.getInstance("PKCS12");
        loaded.load(new ByteArrayInputStream(ksBytes), "store-password".toCharArray());
        SecretKey recovered = (SecretKey) loaded.getKey("aes-key-alias", "ks-password".toCharArray());
        System.out.println("Recovered key algorithm: " + recovered.getAlgorithm());
        System.out.println("Keys match: " + java.util.Arrays.equals(aesKey.getEncoded(), recovered.getEncoded()));
    }
}
```

---

## Step 8: Capstone — Full JCA Demo

```java
import java.security.*;
import java.security.spec.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import java.util.Base64;

public class Main {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("EC");
        kpg.initialize(new ECGenParameterSpec("secp256r1"));
        KeyPair kp = kpg.generateKeyPair();
        System.out.println("EC P-256 KeyPair generated");
        System.out.println("Public key: " + Base64.getEncoder().encodeToString(kp.getPublic().getEncoded()).substring(0,32) + "...");
        
        byte[] data = "Hello, JCA!".getBytes();
        Signature signer = Signature.getInstance("SHA256withECDSA");
        signer.initSign(kp.getPrivate());
        signer.update(data);
        byte[] sig = signer.sign();
        System.out.println("Signature (SHA256withECDSA): " + Base64.getEncoder().encodeToString(sig).substring(0,32) + "...");
        
        Signature verifier = Signature.getInstance("SHA256withECDSA");
        verifier.initVerify(kp.getPublic());
        verifier.update(data);
        System.out.println("Signature valid: " + verifier.verify(sig));
        
        SecretKeyFactory skf = SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256");
        PBEKeySpec spec = new PBEKeySpec("password".toCharArray(), "salt12345".getBytes(), 600000, 256);
        byte[] derived = skf.generateSecret(spec).getEncoded();
        System.out.println("PBKDF2 (600k iter): " + Base64.getEncoder().encodeToString(derived).substring(0,32) + "...");
        
        KeyGenerator kg = KeyGenerator.getInstance("AES");
        kg.init(256);
        SecretKey aesKey = kg.generateKey();
        byte[] iv = new byte[12]; new SecureRandom().nextBytes(iv);
        GCMParameterSpec gcmSpec = new GCMParameterSpec(128, iv);
        Cipher enc = Cipher.getInstance("AES/GCM/NoPadding");
        enc.init(Cipher.ENCRYPT_MODE, aesKey, gcmSpec);
        byte[] ciphertext = enc.doFinal("Secret message!".getBytes());
        System.out.println("AES-GCM ciphertext: " + Base64.getEncoder().encodeToString(ciphertext));
        Cipher dec = Cipher.getInstance("AES/GCM/NoPadding");
        dec.init(Cipher.DECRYPT_MODE, aesKey, gcmSpec);
        System.out.println("AES-GCM decrypted: " + new String(dec.doFinal(ciphertext)));
    }
}
```

```bash
javac /tmp/Main.java -d /tmp && java -cp /tmp Main
```

📸 **Verified Output:**
```
EC P-256 KeyPair generated
Public key: MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcD...
Signature (SHA256withECDSA): MEUCIEse5xWrkev1M0Ct/m3ZFk9I4eU9...
Signature valid: true
PBKDF2 (600k iter): fJPvbEeh/QVtgkiqcfP5SysLdm/gOBKN...
AES-GCM ciphertext: DCqhBreXPwItM1EvR+0TuZIUJsl0RGUrZ8T6ftHRzg==
AES-GCM decrypted: Secret message!
```

---

## Summary

| Algorithm | Class | Standard |
|---|---|---|
| EC P-256 keygen | `KeyPairGenerator("EC")` | NIST FIPS 186-4 |
| ECDSA sign/verify | `Signature("SHA256withECDSA")` | RFC 6090 |
| ECDH key agreement | `KeyAgreement("ECDH")` | RFC 5114 |
| Password hashing | `SecretKeyFactory("PBKDF2WithHmacSHA256")` | RFC 8018, 600k iterations |
| Symmetric encryption | `Cipher("AES/GCM/NoPadding")` | NIST SP 800-38D |
| Keystore format | `KeyStore("PKCS12")` | RFC 7292 |
| Secure random | `SecureRandom` | NIST SP 800-90A |
| Key derivation | HKDF via `Mac("HmacSHA256")` | RFC 5869 |
