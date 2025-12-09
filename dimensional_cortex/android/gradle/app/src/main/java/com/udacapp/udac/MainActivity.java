package com.udacapp.udac;

import android.content.Intent;
import android.content.res.Configuration;
import android.os.Bundle;
import android.system.Os;
import android.system.ErrnoException;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.LinearLayout;

import androidx.appcompat.app.AppCompatActivity;

import com.chaquo.python.Kwarg;
import com.chaquo.python.PyException;
import com.chaquo.python.PyObject;
import com.chaquo.python.Python;
import com.chaquo.python.android.AndroidPlatform;

import java.util.Iterator;
import java.util.List;

import org.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONException;

import com.udacapp.udac.R;


public class MainActivity extends AppCompatActivity {

    private String TAG = "MainActivity";
    private static PyObject pythonApp;

    /**
     * Called by Toga/BeeWare when Python app initializes.
     */
    @SuppressWarnings("unused")
    public static void setPythonApp(Object app) {
        Log.d("MainActivity", "setPythonApp called");
        if (app != null) {
            pythonApp = PyObject.fromJava(app);
            Log.d("MainActivity", "pythonApp set successfully");
        }
    }

    public static MainActivity singletonThis;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        Log.d(TAG, "onCreate() start");

        try {
            setTheme(R.style.AppTheme);
            super.onCreate(savedInstanceState);

            LinearLayout layout = new LinearLayout(this);
            layout.setOrientation(LinearLayout.VERTICAL);
            this.setContentView(layout);
            singletonThis = this;

            // Handle environment variables
            String environStr = getIntent().getStringExtra("org.beeware.ENVIRON");
            if (environStr != null) {
                try {
                    JSONObject environJson = new JSONObject(environStr);
                    for (Iterator<String> it = environJson.keys(); it.hasNext(); ) {
                        String key = it.next();
                        String value = environJson.getString(key);
                        Os.setenv(key, value, true);
                    }
                } catch (JSONException | ErrnoException e) {
                    Log.e(TAG, "Error setting environment: " + e.getMessage());
                }
            }

            // Start Python
            Python py;
            if (Python.isStarted()) {
                Log.d(TAG, "Python already started");
                py = Python.getInstance();
            } else {
                Log.d(TAG, "Starting Python...");
                try {
                    AndroidPlatform platform = new AndroidPlatform(this);
                    platform.redirectStdioToLogcat();
                    Python.start(platform);
                    py = Python.getInstance();
                    Log.d(TAG, "Python started successfully");
                } catch (Exception e) {
                    Log.e(TAG, "Failed to start Python: " + e.getMessage());
                    e.printStackTrace();
                    return;
                }
            }

            // Run the module as __main__ which triggers __main__.py
            // This will call main().main_loop() properly
            String mainModule = getString(R.string.main_module);
            Log.d(TAG, "Running module: " + mainModule);

            try {
                // This runs dimensional_cortex/__main__.py
                py.getModule("runpy").callAttr(
                    "run_module",
                    mainModule,
                    new Kwarg("run_name", "__main__"),
                    new Kwarg("alter_sys", true)
                );
                Log.d(TAG, "Module executed");
            } catch (PyException e) {
                Log.e(TAG, "Python error: " + e.getMessage());
                e.printStackTrace();
            }

            userCode("onCreate");
            Log.d(TAG, "onCreate() complete");

        } catch (Exception e) {
            Log.e(TAG, "onCreate() FATAL: " + e.getMessage());
            e.printStackTrace();
        }
    }

    @Override
    protected void onStart() {
        Log.d(TAG, "onStart()");
        super.onStart();
        userCode("onStart");
    }

    @Override
    protected void onResume() {
        Log.d(TAG, "onResume()");
        super.onResume();
        userCode("onResume");
    }

    @Override
    protected void onPause() {
        Log.d(TAG, "onPause()");
        super.onPause();
        userCode("onPause");
    }

    @Override
    protected void onStop() {
        Log.d(TAG, "onStop()");
        super.onStop();
        userCode("onStop");
    }

    @Override
    protected void onDestroy() {
        Log.d(TAG, "onDestroy()");
        super.onDestroy();
        userCode("onDestroy");
    }

    @Override
    protected void onRestart() {
        Log.d(TAG, "onRestart()");
        super.onRestart();
        userCode("onRestart");
    }

    @Override
    public void onTopResumedActivityChanged(boolean isTopResumedActivity) {
        super.onTopResumedActivityChanged(isTopResumedActivity);
        userCode("onTopResumedActivityChanged", isTopResumedActivity);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        userCode("onActivityResult", requestCode, resultCode, data);
    }

    @Override
    public void onConfigurationChanged(Configuration newConfig) {
        super.onConfigurationChanged(newConfig);
        userCode("onConfigurationChanged", newConfig);
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem menuitem) {
        PyObject result = userCode("onOptionsItemSelected", menuitem);
        return result != null && result.toBoolean();
    }

    @Override
    public boolean onPrepareOptionsMenu(Menu menu) {
        PyObject result = userCode("onPrepareOptionsMenu", menu);
        return result != null && result.toBoolean();
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        userCode("onRequestPermissionsResult", requestCode, permissions, grantResults);
    }

    private PyObject userCode(String methodName, Object... args) {
        if (pythonApp == null) {
            return null;
        }

        try {
            if (pythonApp.containsKey(methodName)) {
                return pythonApp.callAttr(methodName, args);
            }
        } catch (PyException e) {
            if (!e.getMessage().startsWith("NotImplementedError")) {
                Log.e(TAG, "Error in " + methodName + ": " + e.getMessage());
            }
        } catch (Exception e) {
            Log.e(TAG, "Error in " + methodName + ": " + e.getMessage());
        }
        return null;
    }
}
