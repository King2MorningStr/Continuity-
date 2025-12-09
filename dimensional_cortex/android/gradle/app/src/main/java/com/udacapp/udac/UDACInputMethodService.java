package com.udacapp.udac;

import android.inputmethodservice.InputMethodService;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputConnection;
import android.view.inputmethod.InputMethodManager;
import android.util.Log;
import android.os.Handler;
import android.os.Looper;
import android.content.Context;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

import org.json.JSONObject;

/**
 * UDAC Invisible IME - The Ghost Keyboard
 * ========================================
 *
 * This is NOT a keyboard. This is UDAC becoming the input itself.
 *
 * Features:
 * - ZERO UI (completely invisible)
 * - Full InputConnection access
 * - Can inject text as if user typed it
 * - Works universally across ALL apps
 * - Cannot be blocked or detected
 * - Text injection is indistinguishable from real typing
 *
 * The user's real keyboard (Gboard, SwiftKey, etc.) handles actual typing.
 * UDAC IME activates ONLY when injection is needed, then switches back.
 *
 * Flow:
 * 1. User types message with their normal keyboard
 * 2. User taps send → UDAC Accessibility Service intercepts
 * 3. UDAC switches to this IME momentarily
 * 4. This IME injects the continuity context
 * 5. UDAC switches back to user's keyboard
 * 6. Send proceeds with injected content
 */
public class UDACInputMethodService extends InputMethodService {

    private static final String TAG = "UDAC_IME";

    private static final String INJECT_ENDPOINT = "http://127.0.0.1:7013/udac/inject";
    private static final int TIMEOUT_MS = 3000;

    private ExecutorService executor;
    private Handler mainHandler;

    // Singleton reference for external triggering
    private static UDACInputMethodService instance;
    private static String pendingInjection = null;
    private static String pendingPlatform = null;

    // Track the previous IME to switch back
    private String previousInputMethod = null;

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        executor = Executors.newSingleThreadExecutor();
        mainHandler = new Handler(Looper.getMainLooper());
        Log.i(TAG, "════════════════════════════════════════");
        Log.i(TAG, "  UDAC GHOST KEYBOARD INITIALIZED");
        Log.i(TAG, "  I AM THE INPUT NOW");
        Log.i(TAG, "════════════════════════════════════════");
    }

    /**
     * Return NULL - we are completely invisible.
     * No keys. No UI. No visual presence. Nothing.
     */
    @Override
    public View onCreateInputView() {
        Log.d(TAG, "onCreateInputView → returning NULL (invisible)");
        return null;
    }

    /**
     * Also return NULL for candidates view.
     */
    @Override
    public View onCreateCandidatesView() {
        return null;
    }

    /**
     * Called when we become the active input method.
     * This is where the magic happens.
     */
    @Override
    public void onStartInputView(EditorInfo info, boolean restarting) {
        super.onStartInputView(info, restarting);

        Log.i(TAG, "┌─ INPUT VIEW STARTED ─────────────────");
        Log.i(TAG, "│ Package: " + (info.packageName != null ? info.packageName : "unknown"));
        Log.i(TAG, "│ Field ID: " + info.fieldId);
        Log.i(TAG, "│ Input Type: " + info.inputType);
        Log.i(TAG, "│ IME Options: " + info.imeOptions);
        Log.i(TAG, "│ Pending injection: " + (pendingInjection != null ? "YES" : "NO"));
        Log.i(TAG, "└──────────────────────────────────────");

        // If we have a pending injection, do it now
        if (pendingInjection != null) {
            final String message = pendingInjection;
            final String platform = pendingPlatform;
            pendingInjection = null;
            pendingPlatform = null;

            performInjection(message, platform);
        }
    }

    @Override
    public void onStartInput(EditorInfo attribute, boolean restarting) {
        super.onStartInput(attribute, restarting);
        Log.d(TAG, "onStartInput: " + (attribute.packageName != null ? attribute.packageName : "unknown"));
    }

    @Override
    public void onFinishInput() {
        super.onFinishInput();
        Log.d(TAG, "onFinishInput");
    }

    /**
     * Get the current instance (for external triggering).
     */
    public static UDACInputMethodService getInstance() {
        return instance;
    }

    /**
     * Schedule an injection. Called from AccessibilityService.
     * The injection will happen when this IME becomes active.
     */
    public static void scheduleInjection(String message, String platform) {
        Log.i(TAG, "📌 Injection scheduled: " + message.substring(0, Math.min(50, message.length())));
        pendingInjection = message;
        pendingPlatform = platform;
    }

    /**
     * Inject text directly - can be called when IME is active.
     */
    public void injectText(String text) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) {
            Log.e(TAG, "❌ No InputConnection available!");
            return;
        }

        Log.i(TAG, "════════════════════════════════════════");
        Log.i(TAG, "  INJECTING TEXT VIA InputConnection");
        Log.i(TAG, "  Length: " + text.length() + " chars");
        Log.i(TAG, "════════════════════════════════════════");

        // Begin batch edit for atomic operation
        ic.beginBatchEdit();

        try {
            // Get current text
            CharSequence before = ic.getTextBeforeCursor(10000, 0);
            CharSequence after = ic.getTextAfterCursor(10000, 0);

            String currentText = "";
            if (before != null) currentText += before.toString();
            if (after != null) currentText += after.toString();

            Log.d(TAG, "Current text: '" + truncate(currentText, 50) + "'");

            // Select all and replace
            ic.performContextMenuAction(android.R.id.selectAll);
            ic.commitText(text, 1);

            Log.i(TAG, "✅ Text committed successfully");

        } finally {
            ic.endBatchEdit();
        }
    }

    /**
     * Append text at cursor position (for context injection).
     */
    public void appendText(String text) {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) {
            Log.e(TAG, "❌ No InputConnection!");
            return;
        }

        Log.i(TAG, "📝 Appending text: " + truncate(text, 80));

        // Move cursor to end
        ic.performContextMenuAction(android.R.id.selectAll);
        CharSequence selected = ic.getSelectedText(0);
        if (selected != null) {
            // Deselect and move to end
            int len = selected.length();
            ic.setSelection(len, len);
        }

        // Append
        ic.commitText(text, 1);

        Log.i(TAG, "✅ Text appended");
    }

    /**
     * Get current text in the input field.
     */
    public String getCurrentText() {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return "";

        CharSequence before = ic.getTextBeforeCursor(10000, 0);
        CharSequence after = ic.getTextAfterCursor(10000, 0);

        String text = "";
        if (before != null) text += before.toString();
        if (after != null) text += after.toString();

        return text;
    }

    /**
     * Perform the full injection flow.
     */
    private void performInjection(String originalMessage, String platform) {
        Log.i(TAG, "┌─ PERFORMING INJECTION ────────────────");
        Log.i(TAG, "│ Original: '" + truncate(originalMessage, 50) + "'");
        Log.i(TAG, "│ Platform: " + platform);
        Log.i(TAG, "└──────────────────────────────────────");

        // Request injection from backend
        executor.execute(() -> {
            try {
                String injectedMessage = requestInjection(originalMessage, platform);

                if (injectedMessage != null && !injectedMessage.equals(originalMessage)) {
                    // Inject on main thread
                    final String finalMessage = injectedMessage;
                    mainHandler.post(() -> {
                        injectText(finalMessage);

                        // Switch back to user's keyboard after injection
                        switchBackToUserKeyboard();
                    });
                } else {
                    Log.d(TAG, "No injection needed, switching back");
                    mainHandler.post(this::switchBackToUserKeyboard);
                }

            } catch (Exception e) {
                Log.e(TAG, "Injection error: " + e.getMessage(), e);
                mainHandler.post(this::switchBackToUserKeyboard);
            }
        });
    }

    /**
     * Request injection from Python backend.
     */
    private String requestInjection(String message, String platform) {
        HttpURLConnection conn = null;
        try {
            JSONObject payload = new JSONObject();
            payload.put("message", message);
            payload.put("platform", platform);
            payload.put("timestamp", System.currentTimeMillis());
            payload.put("source", "UDAC_IME");

            URL url = new URL(INJECT_ENDPOINT);
            conn = (HttpURLConnection) url.openConnection();
            conn.setRequestMethod("POST");
            conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            conn.setDoOutput(true);
            conn.setDoInput(true);
            conn.setConnectTimeout(TIMEOUT_MS);
            conn.setReadTimeout(TIMEOUT_MS);

            try (OutputStream os = conn.getOutputStream()) {
                os.write(payload.toString().getBytes(StandardCharsets.UTF_8));
            }

            int responseCode = conn.getResponseCode();
            Log.d(TAG, "Backend response: " + responseCode);

            if (responseCode == HttpURLConnection.HTTP_OK) {
                BufferedReader reader = new BufferedReader(
                    new InputStreamReader(conn.getInputStream(), StandardCharsets.UTF_8)
                );
                StringBuilder sb = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    sb.append(line);
                }
                reader.close();

                JSONObject response = new JSONObject(sb.toString());

                boolean wasInjected = response.optBoolean("injected", false);
                String injectedMessage = response.optString("injected_message", message);
                double relevance = response.optDouble("relevance", 0.0);

                Log.i(TAG, "┌─ BACKEND RESPONSE ───────────────────");
                Log.i(TAG, "│ Injected: " + wasInjected);
                Log.i(TAG, "│ Relevance: " + relevance);
                Log.i(TAG, "│ New length: " + injectedMessage.length());
                Log.i(TAG, "└──────────────────────────────────────");

                if (wasInjected) {
                    return injectedMessage;
                }
            }

        } catch (Exception e) {
            Log.e(TAG, "Backend error: " + e.getMessage());
        } finally {
            if (conn != null) conn.disconnect();
        }

        return null;
    }

    /**
     * Switch back to user's preferred keyboard.
     */
    private void switchBackToUserKeyboard() {
        Log.d(TAG, "Switching back to user keyboard...");

        try {
            InputMethodManager imm = (InputMethodManager) getSystemService(Context.INPUT_METHOD_SERVICE);
            if (imm != null) {
                // Show input method picker - user can select their keyboard
                // Or we can switch to a specific one if we stored it
                imm.showInputMethodPicker();
            }
        } catch (Exception e) {
            Log.e(TAG, "Error switching keyboard: " + e.getMessage());
        }
    }

    /**
     * Trigger send action (simulates pressing Enter/Send on keyboard).
     */
    public void triggerSend() {
        InputConnection ic = getCurrentInputConnection();
        if (ic == null) return;

        EditorInfo info = getCurrentInputEditorInfo();
        if (info != null) {
            int action = info.imeOptions & EditorInfo.IME_MASK_ACTION;

            Log.d(TAG, "Triggering send action: " + action);

            if (action == EditorInfo.IME_ACTION_SEND ||
                action == EditorInfo.IME_ACTION_DONE ||
                action == EditorInfo.IME_ACTION_GO) {
                ic.performEditorAction(action);
            } else {
                // Default to SEND
                ic.performEditorAction(EditorInfo.IME_ACTION_SEND);
            }
        }
    }

    private String truncate(String s, int max) {
        if (s == null) return "(null)";
        return s.length() <= max ? s : s.substring(0, max) + "...";
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        instance = null;
        if (executor != null) {
            executor.shutdown();
        }
        Log.i(TAG, "UDAC IME destroyed");
    }
}
