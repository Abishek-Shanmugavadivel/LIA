package com.lia.companion;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.os.BatteryManager;
import android.os.Build;
import android.os.VibrationEffect;
import android.os.Vibrator;
import android.speech.tts.TextToSpeech;
import android.util.Log;

import androidx.core.content.ContextCompat;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;

import java.util.Locale;

@CapacitorPlugin(
    name = "LIAAndroidCompanion",
    permissions = {
        @Permission(strings = {Manifest.permission.RECORD_AUDIO}, alias = "microphone")
    }
)
public class LIAAndroidCompanionPlugin extends Plugin implements TextToSpeech.OnInitListener {

    private static final String TAG = "LIAAndroidCompanion";
    private TextToSpeech tts;
    private boolean ttsReady = false;

    @Override
    public void load() {
        super.load();
        try {
            tts = new TextToSpeech(getContext(), this);
        } catch (Exception e) {
            Log.e(TAG, "Failed to initialize TextToSpeech", e);
        }
    }

    @Override
    public void onInit(int status) {
        if (status == TextToSpeech.SUCCESS && tts != null) {
            tts.setLanguage(Locale.US);
            ttsReady = true;
            Log.i(TAG, "Native Android TextToSpeech engine initialized.");
        }
    }

    @PluginMethod
    public void getDeviceTelemetry(PluginCall call) {
        try {
            Context context = getContext();
            JSObject result = new JSObject();

            // Battery Status
            IntentFilter ifilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
            Intent batteryStatus = context.registerReceiver(null, ifilter);
            int level = batteryStatus != null ? batteryStatus.getIntExtra(BatteryManager.EXTRA_LEVEL, -1) : -1;
            int scale = batteryStatus != null ? batteryStatus.getIntExtra(BatteryManager.EXTRA_SCALE, -1) : -1;
            float batteryPct = (level >= 0 && scale > 0) ? (level / (float) scale) * 100 : 85.0f;
            int status = batteryStatus != null ? batteryStatus.getIntExtra(BatteryManager.EXTRA_STATUS, -1) : -1;
            boolean isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL;

            result.put("battery_percentage", Math.round(batteryPct));
            result.put("is_charging", isCharging);
            result.put("device_model", Build.MODEL);
            result.put("manufacturer", Build.MANUFACTURER);
            result.put("android_version", Build.VERSION.RELEASE);
            result.put("sdk_int", Build.VERSION.SDK_INT);

            // Network Connectivity
            ConnectivityManager cm = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
            NetworkInfo activeNetwork = cm != null ? cm.getActiveNetworkInfo() : null;
            boolean isConnected = activeNetwork != null && activeNetwork.isConnectedOrConnecting();
            String connType = (activeNetwork != null) ? activeNetwork.getTypeName() : "WIFI";

            result.put("is_network_connected", isConnected);
            result.put("connection_type", connType);
            result.put("status", "HEALTHY");

            call.resolve(result);
        } catch (Exception e) {
            call.reject("Failed to gather Android telemetry: " + e.getMessage());
        }
    }

    @PluginMethod
    public void openApp(PluginCall call) {
        String packageName = call.getString("package_name");
        String appName = call.getString("app_name", "").toLowerCase();

        if (packageName == null || packageName.isEmpty()) {
            if (appName.contains("chrome")) packageName = "com.android.chrome";
            else if (appName.contains("youtube")) packageName = "com.google.android.youtube";
            else if (appName.contains("whatsapp")) packageName = "com.whatsapp";
            else if (appName.contains("settings")) packageName = "com.android.settings";
            else if (appName.contains("calculator") || appName.contains("calc")) packageName = "com.google.android.calculator";
            else packageName = "com.android.chrome";
        }

        try {
            Context context = getContext();
            Intent launchIntent = context.getPackageManager().getLaunchIntentForPackage(packageName);
            if (launchIntent != null) {
                launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(launchIntent);
                JSObject ret = new JSObject();
                ret.put("success", true);
                ret.put("message", "Opened app " + packageName);
                call.resolve(ret);
            } else {
                call.reject("App with package '" + packageName + "' is not installed on this Android device.");
            }
        } catch (Exception e) {
            call.reject("Could not launch app: " + e.getMessage());
        }
    }

    @PluginMethod
    public void vibrateDevice(PluginCall call) {
        int durationMs = call.getInt("duration", 100);
        try {
            Vibrator v = (Vibrator) getContext().getSystemService(Context.VIBRATOR_SERVICE);
            if (v != null && v.hasVibrator()) {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    v.vibrate(VibrationEffect.createOneShot(durationMs, VibrationEffect.DEFAULT_AMPLITUDE));
                } else {
                    v.vibrate(durationMs);
                }
            }
            JSObject ret = new JSObject();
            ret.put("success", true);
            call.resolve(ret);
        } catch (Exception e) {
            call.reject("Vibration failed: " + e.getMessage());
        }
    }

    @PluginMethod
    public void speakText(PluginCall call) {
        String text = call.getString("text");
        if (text == null || text.isEmpty()) {
            call.reject("No text provided for native speech synthesis.");
            return;
        }

        if (ttsReady && tts != null) {
            tts.speak(text, TextToSpeech.QUEUE_FLUSH, null, "LIA_NATIVE_TTS");
            JSObject ret = new JSObject();
            ret.put("success", true);
            ret.put("spoken", text);
            call.resolve(ret);
        } else {
            call.reject("Native TextToSpeech engine not ready.");
        }
    }

    @PluginMethod
    public void checkMicPermission(PluginCall call) {
        boolean granted = ContextCompat.checkSelfPermission(getContext(), Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED;
        JSObject ret = new JSObject();
        ret.put("granted", granted);
        call.resolve(ret);
    }
}
