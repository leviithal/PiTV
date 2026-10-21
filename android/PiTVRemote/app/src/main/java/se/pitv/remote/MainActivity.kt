package se.pitv.remote

import android.app.Activity
import android.app.AlertDialog
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import org.json.JSONObject
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private val bg = Color.rgb(11, 16, 32)
    private val card = Color.rgb(35, 47, 71)
    private val accent = Color.rgb(101, 77, 198)
    private val white = Color.WHITE
    private val muted = Color.rgb(171, 185, 210)
    private val executor = Executors.newSingleThreadExecutor()
    private lateinit var prefs: SecurePrefs
    private lateinit var outer: LinearLayout
    private lateinit var status: TextView
    private var api: PiApi? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs = SecurePrefs(this)
        window.statusBarColor = bg
        window.navigationBarColor = bg
        if (prefs.host.isNotBlank() && prefs.token() != null) showRemote() else showSetup()
    }

    private fun dp(n: Int): Int = (n * resources.displayMetrics.density).toInt()
    private fun rounded(color: Int, radius: Int = 15): GradientDrawable =
        GradientDrawable().apply { setColor(color); cornerRadius = dp(radius).toFloat() }
    private fun pad(v: View, l: Int, t: Int, r: Int, b: Int) {
        v.setPadding(dp(l), dp(t), dp(r), dp(b))
    }
    private fun label(text: String, size: Float = 16f, color: Int = white, bold: Boolean = false): TextView =
        TextView(this).apply {
            this.text = text
            textSize = size
            setTextColor(color)
            gravity = Gravity.CENTER_VERTICAL
            if (bold) setTypeface(typeface, Typeface.BOLD)
        }
    private fun vertical(): LinearLayout = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
    private fun horizontal(): LinearLayout = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
    private fun item(v: View, height: Int = -2, weight: Float = 0f): LinearLayout.LayoutParams =
        LinearLayout.LayoutParams(if (weight > 0) 0 else -1, if (height >= 0) dp(height) else height, weight).apply {
            setMargins(dp(4), dp(4), dp(4), dp(4))
        }.also { v.layoutParams = it }
    private fun button(text: String, color: Int = card, press: () -> Unit): Button =
        Button(this).apply {
            this.text = text
            textSize = 16f
            setTextColor(white)
            isAllCaps = false
            background = rounded(color)
            minHeight = dp(58)
            setOnClickListener { press() }
        }
    private fun edit(hint: String, value: String = "", secret: Boolean = false): EditText =
        EditText(this).apply {
            setText(value)
            this.hint = hint
            setHintTextColor(muted)
            setTextColor(white)
            textSize = 15f
            background = rounded(card)
            pad(this, 12, 8, 12, 8)
            inputType = if (secret) 129 else 1 // password; regular text
            isSingleLine = true
        }
    private fun root(title: String, description: String) {
        outer = vertical()
        outer.setBackgroundColor(bg)
        pad(outer, 12, 14, 12, 10)
        setContentView(outer)
        val h = label(title, 25f, white, true)
        item(h); outer.addView(h)
        val p = label(description, 13f, muted)
        item(p);outer.addView(p)
        status = label("", 13f, muted)
        item(status);outer.addView(status)
    }
    private fun showSetup() {
        api = null
        root("PiTV Remote", "Anslut till din Raspberry Pi med HTTPS och certifikatkontroll")
        val scroll = ScrollView(this)
        outer.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        val content = vertical(); scroll.addView(content)
        val ip = edit("Pi IP, till exempel 192.168.1.50", prefs.host)
        content.addView(ip, item(ip, 56))
        val token = edit("API-nyckel från Pi:n", prefs.token() ?: "", true)
        content.addView(token, item(token, 56))
        val fp = edit("Certifikat SHA-256 (64 tecken)", prefs.fingerprint)
        content.addView(fp, item(fp, 76))
        val tip = label("På Pi:n: bash ~/pi-tv-v3/show-connection.sh\n\nKopiera uppgifterna därifrån. Använd Pi:ns vanliga IPv4-adress, utan http:// eller portnummer.", 14f, muted)
        item(tip); content.addView(tip)
        val connect = button("Anslut säkert",accent) {
            val h = ip.text.toString().trim()
            val t = token.text.toString().trim()
            val f = fp.text.toString().trim()
            try {
                val candidate = PiApi(h,t,f)
                status.text = "Kontrollerar certifikat och anslutning …"
                executor.execute {
                    try {
                        candidate.status()
                        runOnUiThread {
                            prefs.host = h
                            prefs.fingerprint = f
                            prefs.storeToken(t)
                            showRemote()
                        }
                    } catch (ex: Exception) {
                        runOnUiThread { status.text = "Kunde inte ansluta: ${safeError(ex)}" }
                    }
                }
            } catch (ex: Exception) { status.text = safeError(ex) }
        }
        item(connect, 60); content.addView(connect)
    }

    private fun safeError(ex: Exception): String {
        // Avoid showing server URL with credentials: credentials are never in URLs here.
        val message = ex.message ?: "Okänt fel"
        return message.take(125)
    }
    private fun send(action: String, extras: JSONObject = JSONObject()) {
        val instance = api ?: return
        executor.execute {
            try {
                val result = instance.action(action, extras)
                runOnUiThread {
                    status.text = if (result.optBoolean("focus_confirmed", true) == false) "Skickat • fönsterfokus ej verifierat" else "✓ Kommando skickat"
                }
            } catch (ex: Exception) {
                runOnUiThread { status.text = "Fel: ${safeError(ex)}" }
            }
        }
    }
    private fun addRow(parent: LinearLayout, vararg pairs: Pair<String,String>, highlight: String = "") {
        val row = horizontal()
        parent.addView(row, LinearLayout.LayoutParams(-1,-2))
        pairs.forEach { (text,action) ->
            if (text.isEmpty()) {
                val spacer = View(this)
                row.addView(spacer, LinearLayout.LayoutParams(0,dp(65),1f))
            } else {
                val b = button(text, if (action == highlight) accent else card) { send(action) }
                row.addView(b, LinearLayout.LayoutParams(0,dp(65),1f).apply { setMargins(dp(4),dp(4),dp(4),dp(4)) })
            }
        }
    }
    private fun showRemote() {
        try { api = PiApi(prefs.host, prefs.token() ?: "",prefs.fingerprint) }
        catch (_: Exception) { showSetup(); return }
        root("🎬 PiTV Remote", "Native Android-fjärrkontroll • Netflix & Disney+ finns på TV:n")
        status.text = "Ansluter …"
        val settings = button("⚙  Anslutningsinställningar") { showSetup() }
        outer.addView(settings, item(settings, 52))
        val scroll = ScrollView(this)
        outer.addView(scroll, LinearLayout.LayoutParams(-1,0,1f))
        val body = vertical(); scroll.addView(body)
        val spacer = label("Navigering", 16f, muted,true)
        body.addView(spacer,item(spacer))
        addRow(body,"" to "", "▲" to "up", "" to "")
        addRow(body,"◀" to "left", "OK" to "ok", "▶" to "right", highlight="ok")
        addRow(body,"" to "", "▼" to "down", "" to "")
        val media = label("Uppspelning & ljud",16f,muted,true)
        body.addView(media,item(media))
        addRow(body,"Vol −" to "volumedown", "⏯" to "space", "Vol +" to "volumeup")
        addRow(body,"Tyst" to "mute", "Avbryt" to "esc", "◎ Val" to "focus")
        val header = label("Reservstyrning",16f,muted,true)
        body.addView(header,item(header))
        val touch = TextView(this).apply {
            text = "Dra fingret för muspekare\nTryck för musklick"
            textSize = 16f
            gravity = Gravity.CENTER
            setTextColor(muted)
            background = rounded(Color.rgb(26,37,63))
        }
        body.addView(touch,item(touch,110))
        var x=0f; var y=0f;var moved=false;var last=0L
        touch.setOnTouchListener { _,event ->
            when(event.actionMasked) {
                MotionEvent.ACTION_DOWN -> { x=event.x;y=event.y;moved=false;true }
                MotionEvent.ACTION_MOVE -> {
                    val dx=((event.x-x)*1.6f).toInt().coerceIn(-160,160)
                    val dy=((event.y-y)*1.6f).toInt().coerceIn(-160,160)
                    if(kotlin.math.abs(dx)+kotlin.math.abs(dy)>3) moved=true
                    if ((dx!=0 || dy!=0) && System.currentTimeMillis()-last>85) {
                        send("move", JSONObject().put("dx",dx).put("dy",dy))
                        x=event.x;y=event.y;last=System.currentTimeMillis()
                    }
                    true
                }
                MotionEvent.ACTION_UP -> { if(!moved)send("click");true }
                else -> true
            }
        }
        addRow(body,"Scroll ↑" to "scrollup","Musklick" to "click","Scroll ↓" to "scrolldown")
        val typeButton = button("⌨  Skriv text på TV:n") {
            val input = EditText(this)
            input.setSingleLine(true)
            AlertDialog.Builder(this).setTitle("Skriv på TV:n")
                .setView(input).setNegativeButton("Avbryt",null)
                .setPositiveButton("Skicka") { _,_ ->
                    val value=input.text.toString()
                    if(value.isNotBlank()) send("type",JSONObject().put("value",value.take(140)))
                }.show()
        }
        body.addView(typeButton,item(typeButton,56))
        // Fixed Back button: works without scrolling in the phone app.
        val back=button("↶  Bakåt",accent) { send("back") }
        outer.addView(back,item(back,60))
        executor.execute {
            try {
                val s=api?.status()
                runOnUiThread {
                    status.text=if(s?.optBoolean("chromium_running")==true) "● Ansluten • Chromium körs" else "● Ansluten • Chromium ej bekräftad"
                }
            } catch (ex: Exception) { runOnUiThread { status.text="Offline: ${safeError(ex)}" } }
        }
    }

    @Deprecated("Use built-in phone back for PiTV back navigation")
    override fun onBackPressed() {
        if(api!=null)send("back") else super.onBackPressed()
    }

    override fun onDestroy() { executor.shutdownNow(); super.onDestroy() }
}
