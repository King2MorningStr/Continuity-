UDAC Crash Trap is enabled.
If the app crashes, a Python traceback will be written to an on-device log file.

Primary location (Android): $HOME/udac_logs/udac_crash.log
Fallback location: platformdirs user_data_dir('UDAC Portal','UDAC')/udac_crash.log

To view:
- Use adb: adb shell run-as <your.package> cat files/udac_logs/udac_crash.log
- Or browse app files if you have a file explorer with app-private access.
