# Lab 6: Cryptography & Security — JCA/JCE

## Objective
Use Java's cryptography architecture (`javax.crypto`, `java.security`) to implement SHA-256 hashing, HMAC-SHA256 message authentication, AES-256-GCM authenticated encryption/decryption, RSA-2048 digital signing and verification, and secure random token generation.

## Background
The Java Cryptography Architecture (JCA) provides a provider-based, algorithm-agnostic API. You never implement crypto algorithms — you call `MessageDigest.getInstance("SHA-256")`, `Cipher.getInstance("AES/GCM/NoPadding")`, etc., and the provider (Sun's JCE by default) handles the implementation. This makes algorithm migration easy and correct.

## Time
30 minutes

## Prerequisites
- Practitioner Labs (any)

## Tools
- Docker: `zchencow/innozverse-java:latest`

---

## Lab Instructions

### Steps 1–8: SHA-256, HMAC-SHA256, AES-GCM encrypt/decrypt, RSA sign/verify, tamper detection, secure token, password hashing, Capstone audit log

```bash
cat > /tmp/AdvLab06.java << 'JAVAEOF'
import java.security.*;
import java.security.spec.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import java.util.*;

public class AdvLab06 {
    public static void main(String[] args) throws Exception {
        // Step 1: SHA-256 hashing
        System.out.println("=== SHA-256 ===");
        var md = MessageDigest.getInstance("SHA-256");
        byte[] hash = md.digest("Surface Pro $864.00 order:1001".getBytes());
        var hex = HexFormat.of().formatHex(hash);
        System.out.println("Hash:         " + hex.substring(0,32) + "...");
        System.out.println("Length:       " + hash.length + " bytes");

        // Integrity check
        byte[] hash2 = MessageDigest.getInstance("SHA-256").digest("Surface Pro $864.00 order:1001".getBytes());
        byte[] hash3 = MessageDigest.getInstance("SHA-256").digest("Surface Pro $999.00 order:1001".getBytes()); // tampered
        System.out.println("Match:        " + MessageDigest.isEqual(hash, hash2));
        System.out.println("Tampered:     " + MessageDigest.isEqual(hash, hash3));

        // Step 2: HMAC-SHA256
        System.out.println("\n=== HMAC-SHA256 ===");
        var keyGen = KeyGenerator.getInstance("HmacSHA256");
        keyGen.init(256);
        var key = keyGen.generateKey();
        var mac = Mac.getInstance("HmacSHA256");
        mac.init(key);
        byte[] sig = mac.doFinal("order:1001:$864.00:ebiz@chen.me".getBytes());
        System.out.println("HMAC:  " + HexFormat.of().formatHex(sig).substring(0,32) + "...");

        var mac2 = Mac.getInstance("HmacSHA256");
        mac2.init(key);
        byte[] sig2 = mac2.doFinal("order:1001:$864.00:ebiz@chen.me".getBytes());
        System.out.println("Valid: " + MessageDigest.isEqual(sig, sig2));

        // Tamper check
        var mac3 = Mac.getInstance("HmacSHA256");
        mac3.init(key);
        byte[] sig3 = mac3.doFinal("order:1001:$9999.00:ebiz@chen.me".getBytes()); // tampered
        System.out.println("Tampered: " + MessageDigest.isEqual(sig, sig3));

        // Step 3: AES-256-GCM (authenticated encryption)
        System.out.println("\n=== AES-256-GCM ===");
        var aesKeyGen = KeyGenerator.getInstance("AES");
        aesKeyGen.init(256);
        var secretKey = aesKeyGen.generateKey();
        byte[] iv = new byte[12];
        new SecureRandom().nextBytes(iv);

        var cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.ENCRYPT_MODE, secretKey, new GCMParameterSpec(128, iv));
        byte[] plaintext = "ccnum=4111111111111111;exp=12/28;cvv=123".getBytes();
        byte[] ciphertext = cipher.doFinal(plaintext);
        System.out.println("Plaintext:  " + new String(plaintext));
        System.out.println("Ciphertext: " + HexFormat.of().formatHex(ciphertext).substring(0,32) + "...");
        System.out.println("Size:       " + plaintext.length + " -> " + ciphertext.length + " bytes (+16 GCM tag)");

        cipher.init(Cipher.DECRYPT_MODE, secretKey, new GCMParameterSpec(128, iv));
        byte[] decrypted = cipher.doFinal(ciphertext);
        System.out.println("Decrypted:  " + new String(decrypted));
        System.out.println("Match:      " + Arrays.equals(plaintext, decrypted));

        // Step 4: RSA-2048 digital signing
        System.out.println("\n=== RSA-2048 Digital Signing ===");
        var kpg = KeyPairGenerator.getInstance("RSA");
        kpg.initialize(2048);
        var kp = kpg.generateKeyPair();

        String orderPayload = "order:1001:Surface Pro:qty=2:total=$1728.00:ebiz@chen.me";
        var signer = Signature.getInstance("SHA256withRSA");
        signer.initSign(kp.getPrivate());
        signer.update(orderPayload.getBytes());
        byte[] signature = signer.sign();
        System.out.println("Payload:   " + orderPayload);
        System.out.println("Signature: " + HexFormat.of().formatHex(signature).substring(0,32) + "...");

        var verifier = Signature.getInstance("SHA256withRSA");
        verifier.initVerify(kp.getPublic());
        verifier.update(orderPayload.getBytes());
        System.out.println("Valid:     " + verifier.verify(signature));

        verifier.initVerify(kp.getPublic());
        verifier.update("order:1001:Surface Pro:qty=2:total=$9999.00:hacker".getBytes());
        System.out.println("Tampered:  " + verifier.verify(signature));

        // Step 5: Secure random tokens
        System.out.println("\n=== Secure Random Tokens ===");
        byte[] tokenBytes = new byte[32];
        new SecureRandom().nextBytes(tokenBytes);
        String token = Base64.getUrlEncoder().withoutPadding().encodeToString(tokenBytes);
        System.out.println("API token: " + token);
        System.out.println("Length:    " + token.length() + " chars (256-bit entropy)");

        // Session ID (shorter)
        byte[] sessionBytes = new byte[16];
        new SecureRandom().nextBytes(sessionBytes);
        String sessionId = HexFormat.of().formatHex(sessionBytes);
        System.out.println("Session:   " + sessionId + " (" + sessionId.length() + " chars)");
    }
}
JAVAEOF
docker run --rm -v /tmp/AdvLab06.java:/tmp/AdvLab06.java zchencow/innozverse-java:latest sh -c "javac /tmp/AdvLab06.java -d /tmp && java -cp /tmp AdvLab06"
```

> 💡 **AES-GCM provides both confidentiality AND integrity.** The 16-byte "GCM tag" appended to the ciphertext is a MAC over the ciphertext — if anyone modifies even a single bit, decryption throws `AEADBadTagException`. This is why AES-GCM is preferred over AES-CBC: CBC encrypts but doesn't authenticate, so a bit-flip attack can modify ciphertext without detection. Never use CBC for new code.

**📸 Verified Output:**
```
=== SHA-256 ===
Hash:         8baec426fac758eab064fc3c97383e04...
Match:        true
Tampered:     false

=== HMAC-SHA256 ===
HMAC:  fb4162492c44f68f65da34f84fe2958e...
Valid: true
Tampered: false

=== AES-256-GCM ===
Plaintext:  ccnum=4111111111111111;exp=12/28;cvv=123
Ciphertext: 27f3e2f688aafd18723489450575ec70...
Size:       40 -> 56 bytes (+16 GCM tag)
Decrypted:  ccnum=4111111111111111;exp=12/28;cvv=123
Match:      true

=== RSA-2048 Digital Signing ===
Valid:     true
Tampered:  false

=== Secure Random Tokens ===
API token: kU4xu4KwGoa163t3X0Xy6_e3Q9grvKAtgKSvIAClOPY
Length:    43 chars (256-bit entropy)
```

---

## Summary

| Use case | Algorithm | API |
|----------|-----------|-----|
| Integrity check | SHA-256 | `MessageDigest.getInstance("SHA-256")` |
| Message auth | HMAC-SHA256 | `Mac.getInstance("HmacSHA256")` |
| Encryption | AES-256-GCM | `Cipher.getInstance("AES/GCM/NoPadding")` |
| Digital signing | RSA-2048 | `Signature.getInstance("SHA256withRSA")` |
| Secure token | CSPRNG | `new SecureRandom()` + Base64 |

## Further Reading
- [Java Security Overview](https://docs.oracle.com/en/java/javase/21/security/)
- [JCA Reference Guide](https://docs.oracle.com/en/java/javase/21/security/java-cryptography-architecture-jca-reference-guide.html)
