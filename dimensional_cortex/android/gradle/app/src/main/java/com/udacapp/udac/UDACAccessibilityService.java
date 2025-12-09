package com.udacapp.udac;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.ComponentName;
import android.content.Context;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.os.Build;

import androidx.core.app.NotificationCompat;
import android.os.Handler;
import android.os.Looper;
import android.provider.Settings;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;
import android.view.inputmethod.InputMethodManager;

import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import org.json.JSONObject;

/**
 * UDAC Accessibility Service - IME Coordinator
 * =============================================
 *
 * This service:
 * 1. Monitors AI chat apps
 * 2. Captures conversations for context building
 * 3. Detects when user is about to send a message
 * 4. Triggers the UDAC IME to inject continuity context
 *
 * The actual text injection happens via UDACInputMethodService.
 * This service just coordinates and captures.
 */
public class UDACAccessibilityService extends AccessibilityService {

    private static final String TAG = "UDAC";
    private static final int NOTIFICATION_ID = 1;
    private static final String CHANNEL_ID = "udac_persistent_channel";

    private static final String EVENT_ENDPOINT = "http://127.0.0.1:7013/udac/event";
    private static final String INJECT_ENDPOINT = "http://127.0.0.1:7013/udac/inject";

    // UDAC IME component name
    private static final String UDAC_IME_ID = "com.udacapp.udac/com.udacapp.udac.UDACInputMethodService";

    // Target packages
    private static final Set<String> TARGET_PACKAGES = new HashSet<>();
    static {
        TARGET_PACKAGES.add("com.openai.chatgpt");
        TARGET_PACKAGES.add("com.anthropic.claude");
        TARGET_PACKAGES.add("ai.perplexity.app.android");
        TARGET_PACKAGES.add("ai.perplexity.app");
        TARGET_PACKAGES.add("com.google.android.apps.bard");
        TARGET_PACKAGES.add("com.google.android.apps.gemini");
        TARGET_PACKAGES.add("com.microsoft.bing");
        TARGET_PACKAGES.add("com.microsoft.copilot");
        TARGET_PACKAGES.add("com.quora.poe");
    }

    private static final Map<String, String> PLATFORM_NAMES = new HashMap<>();
    static {
        PLATFORM_NAMES.put("com.openai.chatgpt", "ChatGPT");
        PLATFORM_NAMES.put("com.anthropic.claude", "Claude");
        PLATFORM_NAMES.put("ai.perplexity.app.android", "Perplexity");
        PLATFORM_NAMES.put("ai.perplexity.app", "Perplexity");
        PLATFORM_NAMES.put("com.google.android.apps.bard", "Gemini");
        PLATFORM_NAMES.put("com.google.android.apps.gemini", "Gemini");
        PLATFORM_NAMES.put("com.microsoft.bing", "Copilot");
        PLATFORM_NAMES.put("com.microsoft.copilot", "Copilot");
        PLATFORM_NAMES.put("com.quora.poe", "Poe");
    }

    private ExecutorService executor;
    private Handler mainHandler;

    // State
    private String currentPackage = "";
    private String lastUserMessage = "";
    private String lastCapturedHash = "";
    private long lastCaptureTime = 0;
    private long lastInjectionTime = 0;

    private static final long DEBOUNCE_MS = 300;
    private static final long INJECTION_COOLDOWN_MS = 3000;

    // Stats
    private int captureCount = 0;
    private int injectionTriggers = 0;

    @Override
    public void onCreate() {
        super.onCreate();
        executor = Executors.newFixedThreadPool(2);
        mainHandler = new Handler(Looper.getMainLooper());
        Log.i(TAG, "════════════════════════════════════════");
        Log.i(TAG, "  UDAC SERVICE CREATED");
        Log.i(TAG, "  Mode: IME Coordinator");
        Log.i(TAG, "════════════════════════════════════════");
    }

    @Override
    public void onServiceConnected() {
        super.onServiceConnected();

        AccessibilityServiceInfo info = getServiceInfo();
        if (info != null) {
            info.eventTypes = AccessibilityEvent.TYPE_VIEW_CLICKED
                    | AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED
                    | AccessibilityEvent.TYPE_VIEW_FOCUSED
                    | AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED;

            info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
            info.flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
                    | AccessibilityServiceInfo.FLAG_RETRIEVE_INTERACTIVE_WINDOWS;
            info.notificationTimeout = 50;
            setServiceInfo(info);
        startPersistentNotification();
        }

        Log.i(TAG, "════════════════════════════════════════");
        Log.i(TAG, "  UDAC SERVICE CONNECTED");
        Log.i(TAG, "  Waiting for IME to be enabled...");
        Log.i(TAG, "════════════════════════════════════════");

        checkIMEEnabled();
        sendCaptureEvent("UDAC_SERVICE", "Accessibility connected", 0);
    }

    private void checkIMEEnabled() {
        String enabledIMEs = Settings.Secure.getString(
            getContentResolver(),
            Settings.Secure.ENABLED_INPUT_METHODS
        );

        boolean imeEnabled = enabledIMEs != null && enabledIMEs.contains("UDACInputMethodService");

        if (imeEnabled) {
            Log.i(TAG, "✅ UDAC IME is enabled");
        } else {
            Log.w(TAG, "⚠️ UDAC IME not enabled yet");
            Log.w(TAG, "   Go to Settings → Language & Input → Keyboards");
            Log.w(TAG, "   Enable 'UDAC Continuity Input'");
        }
    }

    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event == null) return;

        CharSequence pkgSeq = event.getPackageName();
        if (pkgSeq == null) return;

        String packageName = pkgSeq.toString();
        if (!TARGET_PACKAGES.contains(packageName)) {
            return;
        }

        currentPackage = packageName;
        int eventType = event.getEventType();

        switch (eventType) {
            case AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED:
                handleTextChange(event);
                break;

            case AccessibilityEvent.TYPE_VIEW_CLICKED:
                handleClick(event, packageName);
                break;

            case AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED:
                handleContentChange(event, packageName);
                break;
        }
    }

    private void handleTextChange(AccessibilityEvent event) {
        AccessibilityNodeInfo source = event.getSource();
        if (source == null) return;

        try {
            if (source.isEditable()) {
                CharSequence text = source.getText();
                if (text != null) {
                    lastUserMessage = text.toString();
                    Log.d(TAG, "📝 Message: '" + truncate(lastUserMessage, 50) + "'");
                }
            }
        } finally {
            source.recycle();
        }
    }

    private void handleClick(AccessibilityEvent event, String packageName) {
        AccessibilityNodeInfo source = event.getSource();
        if (source == null) return;

        try {
            // Check if this looks like a send button
            if (isSendButton(source)) {
                String platform = PLATFORM_NAMES.getOrDefault(packageName, "Unknown");

                Log.i(TAG, "════════════════════════════════════════");
                Log.i(TAG, "  SEND BUTTON DETECTED");
                Log.i(TAG, "  Platform: " + platform);
                Log.i(TAG, "  Message: '" + truncate(lastUserMessage, 50) + "'");
                Log.i(TAG, "════════════════════════════════════════");

                // Trigger injection via IME
                triggerIMEInjection(lastUserMessage, platform);
            }
        } finally {
            source.recycle();
        }
    }

    private boolean isSendButton(AccessibilityNodeInfo node) {
        String viewId = node.getViewIdResourceName();
        CharSequence contentDesc = node.getContentDescription();
        CharSequence text = node.getText();
        String className = node.getClassName() != null ? node.getClassName().toString() : "";

        // Check ID
        if (viewId != null) {
            String id = viewId.toLowerCase();
            if (id.contains("send") || id.contains("submit") || id.contains("post") ||
                id.contains("arrow") || id.contains("fab") || id.contains("done")) {
                return true;
            }
        }

        // Check description
        if (contentDesc != null) {
            String desc = contentDesc.toString().toLowerCase();
            if (desc.contains("send") || desc.contains("submit") || desc.contains("post") ||
                desc.contains("voice") || desc.contains("arrow")) {
                return true;
            }
        }

        // Check text
        if (text != null) {
            String t = text.toString().toLowerCase();
            if (t.equals("send") || t.equals("submit") || t.equals("post")) {
                return true;
            }
        }

        // Check class
        if (className.contains("FloatingActionButton") || className.contains("ImageButton")) {
            if (contentDesc != null || (viewId != null && !viewId.isEmpty())) {
                return true;
            }
        }

        return false;
    }

    /**
     * Trigger injection via the UDAC IME.
     *
     * This schedules the injection and switches to the UDAC IME,
     * which will then inject the context and switch back.
     */
    private void triggerIMEInjection(String message, String platform) {
        if (message == null || message.trim().isEmpty()) {
            Log.d(TAG, "Empty message, skipping injection");
            return;
        }

        // Check cooldown
        long now = System.currentTimeMillis();
        if (now - lastInjectionTime < INJECTION_COOLDOWN_MS) {
            Log.d(TAG, "Injection cooldown active");
            return;
        }
        lastInjectionTime = now;
        injectionTriggers++;

        Log.i(TAG, "🎯 Triggering IME injection #" + injectionTriggers);

        // Schedule the injection in the IME
        UDACInputMethodService.scheduleInjection(message, platform);

        // Switch to UDAC IME
        switchToUDACIME();
    }

    /**
     * Switch to the UDAC IME programmatically.
     */
    private void switchToUDACIME() {
        try {
            InputMethodManager imm = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
            if (imm != null) {
                // This will show the IME picker if direct switch isn't possible
                // The user may need to select UDAC IME
                imm.showInputMethodPicker();

                Log.i(TAG, "📲 IME picker shown - select UDAC Continuity");
            }
        } catch (Exception e) {
            Log.e(TAG, "Error switching IME: " + e.getMessage());
        }
    }

    private void handleContentChange(AccessibilityEvent event, String packageName) {
        String text = extractText(event);
        if (text == null || text.trim().length() < 5) return;

        // Debounce
        String hash = String.valueOf(text.hashCode());
        long now = System.currentTimeMillis();
        if (hash.equals(lastCapturedHash) && (now - lastCaptureTime) < DEBOUNCE_MS) {
            return;
        }
        lastCapturedHash = hash;
        lastCaptureTime = now;

        // Skip user's own message
        if (lastUserMessage != null && !lastUserMessage.isEmpty()) {
            if (text.contains(lastUserMessage)) {
                return;
            }
        }

        captureCount++;
        String platform = PLATFORM_NAMES.getOrDefault(packageName, packageName);
        Log.d(TAG, "📥 Capture #" + captureCount + " from " + platform);

        sendCaptureEvent(packageName, text, event.getEventType());
    }

    private String extractText(AccessibilityEvent event) {
        StringBuilder sb = new StringBuilder();

        if (event.getText() != null) {
            for (CharSequence t : event.getText()) {
                if (t != null && t.length() > 0) {
                    sb.append(t).append(" ");
                }
            }
        }

        AccessibilityNodeInfo source = event.getSource();
        if (source != null) {
            CharSequence text = source.getText();
            if (text != null) {
                sb.append(text).append(" ");
            }
            source.recycle();
        }

        return sb.toString().trim();
    }

    private void sendCaptureEvent(String sourceApp, String text, int eventType) {
        executor.execute(() -> {
            HttpURLConnection conn = null;
            try {
                JSONObject payload = new JSONObject();
                payload.put("source_app", sourceApp);
                payload.put("text", text);
                payload.put("event_type", eventType);
                payload.put("timestamp", System.currentTimeMillis());

                URL url = new URL(EVENT_ENDPOINT);
                conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                conn.setDoOutput(true);
                conn.setConnectTimeout(5000);
                conn.setReadTimeout(5000);

                try (OutputStream os = conn.getOutputStream()) {
                    os.write(payload.toString().getBytes(StandardCharsets.UTF_8));
                }

                conn.getResponseCode();

            } catch (Exception e) {
                // Backend may not be running
            } finally {
                if (conn != null) conn.disconnect();
            }
        });
    }

    private String truncate(String s, int max) {
        if (s == null) return "(null)";
        return s.length() <= max ? s : s.substring(0, max) + "...";
    }

    @Override
    public void onInterrupt() {
        Log.w(TAG, "Service interrupted");
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (executor != null) {
            executor.shutdown();
        }
        Log.i(TAG, "════════════════════════════════════════");
        Log.i(TAG, "  UDAC SERVICE DESTROYED");
        Log.i(TAG, "  Captures: " + captureCount);
        Log.i(TAG, "  Injections triggered: " + injectionTriggers);
        Log.i(TAG, "════════════════════════════════════════");
    }

    private void startPersistentNotification() {
        NotificationManager nm =
                (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);

        if (nm == null) {
            Log.w(TAG, "NotificationManager is null; cannot start foreground");
            return;
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "UDAC Continuity",
                    NotificationManager.IMPORTANCE_MIN
            );
            channel.setDescription("Keeps UDAC listening for context.");
            nm.createNotificationChannel(channel);
        }

        NotificationCompat.Builder builder =
                new NotificationCompat.Builder(this, CHANNEL_ID)
                        .setContentTitle("UDAC running")
                        .setContentText("Listening for conversation context")
                        .setSmallIcon(R.mipmap.ic_launcher)
                        .setOngoing(true)
                        .setPriority(NotificationCompat.PRIORITY_MIN);

        Notification notification = builder.build();
        startForeground(NOTIFICATION_ID, notification);
    }

}
