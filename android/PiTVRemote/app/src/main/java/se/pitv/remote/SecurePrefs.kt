package se.pitv.remote

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

class SecurePrefs(private val context: Context) {
    private val pref = context.getSharedPreferences("pitv_config", Context.MODE_PRIVATE)
    private val alias = "pitv_v3_device_secret"

    var host: String
        get() = pref.getString("host", "") ?: ""
        set(value) { pref.edit().putString("host", value).apply() }
    var fingerprint: String
        get() = pref.getString("fingerprint", "") ?: ""
        set(value) { pref.edit().putString("fingerprint", value).apply() }

    private fun key(): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        val existing = ks.getKey(alias, null) as? SecretKey
        if (existing != null) return existing
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        generator.init(KeyGenParameterSpec.Builder(alias,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256).build())
        return generator.generateKey()
    }

    fun storeToken(token: String) {
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        val encrypted = cipher.doFinal(token.toByteArray(Charsets.UTF_8))
        pref.edit().putString("iv", Base64.encodeToString(cipher.iv, Base64.NO_WRAP))
            .putString("secret", Base64.encodeToString(encrypted, Base64.NO_WRAP)).apply()
    }

    fun token(): String? {
        val iv = pref.getString("iv", null) ?: return null
        val secret = pref.getString("secret", null) ?: return null
        return try {
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, Base64.decode(iv, Base64.NO_WRAP)))
            String(cipher.doFinal(Base64.decode(secret, Base64.NO_WRAP)), Charsets.UTF_8)
        } catch (_: Exception) { null }
    }
}
