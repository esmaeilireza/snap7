#!/bin/bash

# === SAFE MODE: Never auto-close ===
echo " [STEP 0] Scanning project structure..."

PROJECT_ROOT="/d/Machine learning/NEXT.JS RepoScope/snap 7/snap 7"
UI_FILE="$PROJECT_ROOT/demo/ui/dashboard_ui.py"
MAIN_FILE="$PROJECT_ROOT/demo/scada_dashboard.py"

# Fallback paths if above doesn't exist
if [ ! -f "$UI_FILE" ]; then
    UI_FILE="./ui/dashboard_ui.py"
fi
if [ ! -f "$MAIN_FILE" ]; then
    MAIN_FILE="./scada_dashboard.py"
fi

if [ ! -f "$UI_FILE" ]; then
    echo "[ERROR] Cannot find ui/dashboard_ui.py"
    echo "Searched:"
    echo "  $PROJECT_ROOT/demo/ui/dashboard_ui.py"
    echo "  ./ui/dashboard_ui.py"
    find . -name "dashboard_ui.py" 2>/dev/null | head -5
    read -p "Press Enter to exit..."
    exit 1
fi

echo "[OK] Found UI file: $UI_FILE"
echo "[OK] Found Main file: $MAIN_FILE"

# Install ruff quietly
pip install ruff --quiet 2>/dev/null || true

echo ""
echo " [STEP 1] Full project scan for layout killers..."
echo "----------------------------------------"

# Scan for .place() calls (the #1 layout killer)
PLACE_COUNT=$(grep -r "\.place(" "$PROJECT_ROOT" --include="*.py" 2>/dev/null | wc -l)
echo "  .place() calls found: $PLACE_COUNT"

# Scan for mixed geometry managers in same file
MIXED_FILES=$(grep -rl "\.pack(" "$PROJECT_ROOT" --include="*.py" 2>/dev/null | xargs grep -l "\.grid(" 2>/dev/null | wc -l)
echo "  Files mixing pack()+grid(): $MIXED_FILES"

# Scan for hardcoded pixel sizes
HARDCODED=$(grep -rE "width\s*=\s*[0-9]{3,}|height\s*=\s*[0-9]{3,}" "$UI_FILE" 2>/dev/null | wc -l)
echo "  Hardcoded pixel sizes in UI: $HARDCODED"

echo "----------------------------------------"

if [ "$PLACE_COUNT" -gt 0 ]; then
    echo ""
    echo "❌ CRITICAL: Found $PLACE_COUNT .place() calls — THIS is why your layout breaks!"
    echo "   .place() uses absolute pixels → breaks on resize/DPI/window move"
    echo ""
fi

echo "💥 [STEP 2] Applying surgical layout rewrite..."

# Backup
cp "$UI_FILE" "${UI_FILE}.FINAL_BAK_$(date +%s)"
cp "$MAIN_FILE" "${MAIN_FILE}.FINAL_BAK_$(date +%s)"

python3 << 'PYEOF'
import re
import sys
import os

UI_FILE = sys.argv[1] if len(sys.argv) > 1 else "ui/dashboard_ui.py"
MAIN_FILE = sys.argv[2] if len(sys.argv) > 2 else "scada_dashboard.py"

print(f"\n[INFO] Reading {UI_FILE}...")
with open(UI_FILE, "r", encoding="utf-8") as f:
    ui = f.read()

original_ui = ui

# ============================================================
# NUCLEAR REWRITE: Replace ALL .place() with responsive grid
# ============================================================

# Step 1: Remove every .place(...) call and replace with grid
place_pattern = r'\.place\([^)]*\)'
matches = list(re.finditer(place_pattern, ui))
print(f"[FIX] Found {len(matches)} .place() calls — replacing all with .grid()")

for match in reversed(matches):
    start, end = match.span()
    # Extract the widget variable name from context
    line_start = ui.rfind('\n', 0, start) + 1
    line = ui[line_start:start]
    widget_match = re.search(r'(self\.\w+)', line)
    widget_name = widget_match.group(1) if widget_match else "widget"
    
    # Replace with responsive grid
    replacement = f'.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)  # AUTO-FIXED from .place()'
    ui = ui[:start] + replacement + ui[end:]

# Step 2: Ensure root window has proper grid weights
if "self.grid_rowconfigure" not in ui:
    init_match = re.search(r'def __init__\(self[^)]*\):', ui)
    if init_match:
        sig_end = ui.find('\n', init_match.end())
        indent = "        "
        grid_setup = f'''{indent}# === RESPONSIVE LAYOUT SETUP ===
{indent}self.minsize(1280, 720)
{indent}self.geometry("1400x800")
{indent}self.grid_rowconfigure(0, weight=1)
{indent}self.grid_columnconfigure(0, weight=1)
{indent}# === END RESPONSIVE SETUP ===
'''
        ui = ui[:sig_end+1] + grid_setup + ui[sig_end+1:]
        print("[FIX] Added responsive grid setup to __init__")

# Step 3: Find all Frame creations and ensure they use grid weights
frame_pattern = r'(self\.\w+_frame\s*=\s*(?:ttk|tk)\.Frame\([^)]+\))'
frame_matches = list(re.finditer(frame_pattern, ui))
print(f"[FIX] Found {len(frame_matches)} frames — ensuring grid weights")

for match in reversed(frame_matches):
    frame_code = match.group(1)
    frame_var = re.search(r'self\.(\w+)', frame_code).group(1)
    insert_pos = match.end()
    
    # Add grid weight config after each frame creation
    weight_config = f'''
        self.{frame_var}.grid_rowconfigure(0, weight=1)
        self.{frame_var}.grid_columnconfigure(0, weight=1)
'''
    ui = ui[:insert_pos] + weight_config + ui[insert_pos:]

# Step 4: Add emergency layout validator
validator_code = '''
    def _validate_layout(self):
        """Run after 1 second to catch layout issues."""
        try:
            w, h = self.winfo_width(), self.winfo_height()
            print(f"[LAYOUT CHECK] Window size: {w}x{h}")
            
            if w < 500 or h < 400:
                print("[LAYOUT FIX] Window too small — forcing 1400x800")
                self.geometry("1400x800")
                self.update_idletasks()
            
            # Check all direct children
            for i, child in enumerate(self.winfo_children()):
                cw, ch = child.winfo_width(), child.winfo_height()
                if cw == 1 and ch == 1:
                    print(f"[LAYOUT FIX] Child {i} ({child.winfo_class()}) collapsed — re-gridding")
                    child.grid_forget()
                    child.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
            
            self.update()
        except Exception as e:
            print(f"[LAYOUT ERROR] {e}")
'''

if "_validate_layout" not in ui:
    class_end = ui.rfind('\nclass ')
    if class_end == -1:
        class_end = len(ui)
    last_def = ui.rfind('\n    def ', 0, class_end)
    insert_pos = last_def if last_def != -1 else class_end
    ui = ui[:insert_pos] + validator_code + ui[insert_pos:]
    print("[FIX] Added _validate_layout() method")

# Write back UI file
with open(UI_FILE, "w", encoding="utf-8") as f:
    f.write(ui)
print(f"[OK] {UI_FILE} rewritten successfully")

# ============================================================
# FIX MAIN FILE: Safe DPI + schedule validator
# ============================================================
print(f"\n[INFO] Reading {MAIN_FILE}...")
with open(MAIN_FILE, "r", encoding="utf-8") as f:
    main = f.read()

# Remove ANY existing DPI scaling
main = re.sub(r'dashboard\.tk\.call\("tk", "scaling"[^)]+\)', '# DPI removed — handled safely below', main)

# Inject safe DPI + validator trigger
safe_block = '''
        # === FINAL SAFE DPI + LAYOUT VALIDATION ===
        try:
            dashboard.update_idletasks()
            dpi_raw = dashboard.winfo_fpixels("1i")
            if dpi_raw > 0:
                scale = max(0.75, min(dpi_raw / 72.0, 2.0))  # Tighter clamp
                dashboard.tk.call("tk", "scaling", scale)
                print(f"[INFO] DPI scale: {scale:.2f}")
        except Exception as e:
            print(f"[WARN] DPI fix skipped: {e}")
        
        # Schedule layout validation after window is fully rendered
        dashboard.after(1500, dashboard._validate_layout)
        # === END FINAL FIX ===
'''

inject_target = "def inject_startup_logs():"
if inject_target in main and "FINAL SAFE DPI" not in main:
    pos = main.find(inject_target)
    line_end = main.find('\n', pos)
    main = main[:line_end+1] + safe_block + main[line_end+1:]
    print("[FIX] Injected safe DPI + layout validator trigger")
elif "FINAL SAFE DPI" in main:
    print("[SKIP] Safe DPI block already exists")
else:
    print("[WARN] Could not find inject_startup_logs() — appending at end")
    main += "\n" + safe_block

# Ensure mainloop has safe wrapper
if "dashboard.mainloop()" in main and "KeyboardInterrupt" not in main:
    main = main.replace(
        "dashboard.mainloop()",
        '''try:
        dashboard.mainloop()
    except KeyboardInterrupt:
        print("\\n[INFO] Shutdown requested")
    except Exception as e:
        print(f"[ERROR] Mainloop exception: {e}")
        import traceback; traceback.print_exc()
    finally:
        try: teardown()
        except: pass'''
    )
    print("[FIX] Wrapped mainloop in safe exception handler")

with open(MAIN_FILE, "w", encoding="utf-8") as f:
    f.write(main)
print(f"[OK] {MAIN_FILE} rewritten successfully")

print("\n" + "="*60)
print("✅ SURGICAL REWRITE COMPLETE")
print("="*60)
PYEOF

PYTHON_EXIT=$?

echo ""
echo " [STEP 3] Running ruff format for consistency..."
ruff format --line-length=100 "$UI_FILE" "$MAIN_FILE" 2>/dev/null || echo "[WARN] ruff format skipped"

echo ""
echo "========================================"
if [ $PYTHON_EXIT -eq 0 ]; then
    echo "✅ ALL FIXES APPLIED SUCCESSFULLY"
    echo ""
    echo " NEXT:"
    echo "   python scada_dashboard.py"
    echo ""
    echo " WHAT TO WATCH FOR:"
    echo "   • Terminal should show: [LAYOUT CHECK] Window size: XXXxYYY"
    echo "   • If you see [LAYOUT FIX] → the auto-recovery worked"
    echo "   • The 'NT' button should now be properly positioned"
    echo "   • Left panel should no longer be cut off"
else
    echo "❌ PYTHON PATCHER FAILED (exit code $PYTHON_EXIT)"
    echo "   Scroll up to see the error"
fi

echo ""
echo " Backups created:"
ls -la *.FINAL_BAK_* 2>/dev/null | tail -5 || echo "  (none found)"

echo ""
echo "========================================"
read -p "Press Enter to close this window..."