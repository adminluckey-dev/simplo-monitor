#!/bin/bash
# Launch CMMS in Firefox kiosk mode after the local web server is ready.
set -u

URL="${CMMS_URL:-http://127.0.0.1:8080/}"
HEALTH_URL="${CMMS_HEALTH_URL:-http://127.0.0.1:8080/api/health}"
WAIT_SECS="${CMMS_KIOSK_WAIT:-90}"
DISPLAY_NUM="${DISPLAY:-:0}"
APP_PY="/home/admincmms/simplo-monitor/app.py"
LOG="/home/admincmms/simplo-monitor/data/kiosk-browser.log"

# Snap Firefox stores profiles here (NOT ~/.mozilla)
MOZ_DIR="${HOME}/snap/firefox/common/.mozilla/firefox"
PROFILE_NAME="cmmskiosk"
PROFILE_DIR="${MOZ_DIR}/${PROFILE_NAME}"

export DISPLAY="$DISPLAY_NUM"
if [ -z "${XAUTHORITY:-}" ] && [ -f "$HOME/.Xauthority" ]; then
  export XAUTHORITY="$HOME/.Xauthority"
fi

mkdir -p "$(dirname "$LOG")"
exec >>"$LOG" 2>&1
echo "---- $(date -Iseconds) starting cmms-kiosk ----"

# Keep display awake
xset s off >/dev/null 2>&1 || true
xset s noblank >/dev/null 2>&1 || true
xset -dpms >/dev/null 2>&1 || true

# Ensure backend is running
if ! pgrep -f "$APP_PY" >/dev/null 2>&1; then
  echo "starting app.py"
  nohup python3 "$APP_PY" >>/home/admincmms/simplo-monitor/data/kiosk-app.log 2>&1 &
fi

ready=0
for _ in $(seq 1 "$WAIT_SECS"); do
  if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
    ready=1
    break
  fi
  if curl -fsS --max-time 2 -o /dev/null "$URL" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 1
done
echo "cmms ready=$ready"

# Stop any leftover Firefox so profile lock popup never appears
pkill -f '/snap/firefox/.*/firefox' >/dev/null 2>&1 || true
pkill -x firefox >/dev/null 2>&1 || true
sleep 1
pkill -9 -f '/snap/firefox/.*/firefox' >/dev/null 2>&1 || true
pkill -9 -x firefox >/dev/null 2>&1 || true
sleep 1

# Clear stale profile locks (crash / unclean shutdown)
mkdir -p "$MOZ_DIR" "$PROFILE_DIR"
find "$MOZ_DIR" -maxdepth 2 \( -name lock -o -name .parentlock \) -delete 2>/dev/null || true
rm -f \
  "$PROFILE_DIR/lock" \
  "$PROFILE_DIR/.parentlock" \
  "$HOME/.mozilla/firefox/cmms-kiosk/lock" \
  "$HOME/.mozilla/firefox/cmms-kiosk/.parentlock" \
  2>/dev/null || true

# Register dedicated kiosk profile for snap Firefox
PROFILES_INI="$MOZ_DIR/profiles.ini"
if [ ! -f "$PROFILES_INI" ] || ! grep -q "Name=${PROFILE_NAME}" "$PROFILES_INI" 2>/dev/null; then
  cat >"$PROFILES_INI" <<EOF
[Profile0]
Name=default
IsRelative=1
Path=sc47k2fx.default

[Profile1]
Name=${PROFILE_NAME}
IsRelative=1
Path=${PROFILE_NAME}
Default=1

[General]
StartWithLastProfile=0
Version=2
EOF
fi

# Kiosk prefs — no session restore / crash dialogs / update popups
cat >"$PROFILE_DIR/user.js" <<'EOF'
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("browser.sessionstore.max_resumed_crashes", -1);
user_pref("browser.sessionstore.resume_session_once", false);
user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("browser.startup.page", 0);
user_pref("browser.tabs.warnOnClose", false);
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("toolkit.startup.max_resumed_crashes", -1);
user_pref("full-screen-api.warning.timeout", 0);
user_pref("full-screen-api.warning.delay", 0);
user_pref("browser.rights.3.shown", true);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("app.update.auto", false);
user_pref("app.update.enabled", false);
user_pref("app.update.autoInstallEnabled", false);
user_pref("app.update.silent", true);
user_pref("app.update.doorhanger", false);
user_pref("app.update.download.promptMaxAttempts", 0);
user_pref("app.update.elevation.promptMaxAttempts", 0);
user_pref("app.update.service.enabled", false);
user_pref("app.update.checkInstallTime", false);
user_pref("app.update.interval", 315360000);
user_pref("app.update.promptWaitTime", 315360000);
user_pref("app.update.badgeWaitTime", 315360000);
user_pref("app.update.idletime", 315360000);
user_pref("browser.slowStartup.notificationDisabled", true);
user_pref("browser.messaging-system.askForFeedback", false);
EOF

# Remove session restore files that trigger prompts
rm -f \
  "$PROFILE_DIR/sessionstore.jsonlz4" \
  "$PROFILE_DIR/sessionCheckpoints.json" \
  "$PROFILE_DIR/sessionstore-backups/"* \
  2>/dev/null || true

echo "launching firefox kiosk profile=$PROFILE_DIR url=$URL"
# --no-remote: never reuse/attach to another Firefox instance (avoids "already running" dialog)
# Do NOT use --new-instance with default profile; use dedicated profile path under snap.
exec firefox \
  --kiosk \
  --no-remote \
  --profile "$PROFILE_DIR" \
  "$URL"
