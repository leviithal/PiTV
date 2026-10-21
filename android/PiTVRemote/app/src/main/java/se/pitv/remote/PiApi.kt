package se.pitv.remote

import org.json.JSONObject
import java.net.URL
import java.security.MessageDigest
import java.security.cert.CertificateException
import java.security.cert.X509Certificate
import javax.net.ssl.HttpsURLConnection
import javax.net.ssl.SSLContext
import javax.net.ssl.TrustManager
import javax.net.ssl.X509TrustManager

class PiApi(private val host: String, private val token: String, fingerprint: String) {
    private val fp = fingerprint.filter { it != ':' && !it.isWhitespace() }.uppercase()

    init {
        require(Regex("^[A-Za-z0-9][A-Za-z0-9.-]{0,252}$").matches(host)) { "Ange bara Pi:ns IP eller DNS-namn" }
        require(fp.length == 64 && fp.all { it in '0'..'9' || it in 'A'..'F' }) { "Certifikatets SHA-256 måste vara 64 hextecken" }
        require(token.length in 32..180) { "API-nyckeln ser felaktig ut" }
    }

    private fun connection(path: String, method: String): HttpsURLConnection {
        val trust = object : X509TrustManager {
            override fun getAcceptedIssuers(): Array<X509Certificate> = emptyArray()
            override fun checkClientTrusted(chain: Array<X509Certificate>?, authType: String?) {
                throw CertificateException("Klientcertifikat stöds inte")
            }
            override fun checkServerTrusted(chain: Array<X509Certificate>?, authType: String?) {
                val cert = chain?.firstOrNull() ?: throw CertificateException("Certifikat saknas")
                cert.checkValidity()
                val actual = MessageDigest.getInstance("SHA-256")
                    .digest(cert.encoded).joinToString("") { "%02X".format(it) }
                if (!MessageDigest.isEqual(actual.toByteArray(Charsets.US_ASCII), fp.toByteArray(Charsets.US_ASCII))) {
                    throw CertificateException("Certifikatet matchar inte det som visades på Pi:n")
                }
            }
        }
        val context = SSLContext.getInstance("TLS")
        context.init(null, arrayOf<TrustManager>(trust), null)
        val c = (URL("https://$host:8766$path").openConnection() as HttpsURLConnection)
        c.sslSocketFactory = context.socketFactory
        // Keep the platform hostname/IP verification; server cert includes Pi's IP as SAN.
        c.hostnameVerifier = HttpsURLConnection.getDefaultHostnameVerifier()
        c.requestMethod = method
        c.connectTimeout = 4000
        c.readTimeout = 4000
        c.setRequestProperty("Authorization", "Bearer $token")
        c.setRequestProperty("Accept", "application/json")
        c.instanceFollowRedirects = false
        return c
    }

    private fun request(path: String, method: String, data: JSONObject? = null): JSONObject {
        val c = connection(path, method)
        try {
            if (data != null) {
                c.doOutput = true
                c.setRequestProperty("Content-Type", "application/json; charset=utf-8")
                c.outputStream.use { it.write(data.toString().toByteArray(Charsets.UTF_8)) }
            }
            val status = c.responseCode
            val body = (if (status < 400) c.inputStream else c.errorStream)
                ?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: "{}"
            val json = JSONObject(body)
            if (status !in 200..299) throw IllegalStateException(json.optString("error", "HTTP $status"))
            return json
        } finally { c.disconnect() }
    }

    fun status(): JSONObject = request("/api/status", "GET")
    fun action(name: String, extra: JSONObject = JSONObject()): JSONObject {
        extra.put("action", name)
        return request("/api/action", "POST", extra)
    }
}
