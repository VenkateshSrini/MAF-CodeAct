# Fixing "No Hypervisor was found for Sandbox" — Hyperlight/CodeAct on Windows + WSL2

This guide walks through enabling KVM inside WSL2 so that Hyperlight (used by
Microsoft Agent Framework's CodeAct feature) can create its micro-VM sandbox.

---

## 1. Background: why this happens

Hyperlight needs hardware-assisted virtualization on the host:
- **KVM** on Linux / WSL2
- **WHP (Windows Hypervisor Platform)** on native Windows

Adding `hyperlight-wasm` to `pyproject.toml` only installs the Python
bindings — it does **not** grant access to the underlying virtualization
layer. If that layer isn't available, sandbox/VM creation fails with errors
like:

```
Failed to create sandbox: failed to build ProtoWasmSandbox: No Hypervisor was found for Sandbox
```

Inside **WSL2**, this specifically means the WSL2 VM itself doesn't have
`/dev/kvm` exposed to it, since WSL2 is itself a nested VM under Hyper-V.

---

## 2. Enable nested virtualization (Windows side)

This setting must be edited from **Windows**, not from inside WSL.

1. Open (or create) the file:
   ```
   %USERPROFILE%\.wslconfig
   ```
   Quick way to open it from PowerShell:
   ```powershell
   notepad $env:USERPROFILE\.wslconfig
   ```

2. Add:
   ```ini
   [wsl2]
   nestedVirtualization=true
   ```

3. Save and restart WSL from PowerShell:
   ```powershell
   wsl --shutdown
   ```

**Note:** Nested virtualization for WSL2 only works reliably on **Windows 11**.
On Windows 10 it may stay disabled regardless of this setting.

---

## 3. Update WSL / the WSL2 kernel

Old WSL2 kernels (e.g. `5.15.x`) don't ship KVM as a loadable module at all —
no config change will fix that. You need a kernel in the `6.x` range
(the fix below tested kernel `6.18.33.2-microsoft-standard-WSL2`).

From an **elevated (Administrator) PowerShell**:

```powershell
wsl --update --web-download
wsl --shutdown
```

If the version doesn't change, also update the WSL launcher app itself:

```powershell
winget install Microsoft.WSL
```

Then repeat `wsl --update --web-download` and `wsl --shutdown`.

### Verify the kernel version (inside WSL)
```bash
uname -r
```

---

## 4. Diagnostic checks (inside WSL)

Check that virtualization extensions are visible to the WSL2 VM:
```bash
grep -E "vmx|svm" /proc/cpuinfo
```
You should see `vmx` (Intel) or `svm` (AMD) in `flags`, plus a separate
`vmx flags` line — the presence of `vmx flags` confirms nested virtualization
is actually being passed through from the Windows host.

Check for the KVM kernel modules:
```bash
find /lib/modules/$(uname -r) -iname "kvm*"
```

Check for the device node:
```bash
ls -l /dev/kvm
```

---

## 5. Load the KVM kernel modules

```bash
sudo modprobe kvm
sudo modprobe kvm_intel   # use kvm_amd instead if on an AMD CPU
ls -l /dev/kvm
```

---

## 6. Fix /dev/kvm permissions

By default `/dev/kvm` is often owned by `root:root` with mode `600`, which
blocks your normal user.

1. Check the `kvm` group exists:
   ```bash
   getent group kvm
   ```

2. Add your user to it:
   ```bash
   sudo usermod -aG kvm $USER
   ```

3. Fully restart WSL (group changes require a real restart, not just a new
   terminal):
   ```powershell
   wsl --shutdown
   ```
   Then reopen your distro and confirm:
   ```bash
   groups
   ```

4. If `/dev/kvm` is still `root:root` after restart, add a persistent udev
   rule:
   ```bash
   echo 'KERNEL=="kvm", GROUP="kvm", MODE="0660"' | sudo tee /etc/udev/rules.d/99-kvm.rules
   sudo udevadm control --reload-rules
   sudo udevadm trigger
   ls -l /dev/kvm
   ```

---

## 7. Make KVM modules load automatically on every WSL start

WSL2 doesn't reliably run a full systemd init sequence by default, so
`/etc/modules-load.d/` alone often isn't enough. The dependable method is the
`[boot]` section of `/etc/wsl.conf` (this file lives on the **Linux side**,
unlike `.wslconfig`).

1. Edit the file:
   ```bash
   sudo nano /etc/wsl.conf
   ```

2. Add (merge with any existing sections — don't delete others like
   `[automount]` or `[network]`):
   ```ini
   [boot]
   command = "modprobe kvm; modprobe kvm_intel; chmod 660 /dev/kvm; chown root:kvm /dev/kvm"
   ```

3. Save and exit nano:
   - `Ctrl + O` then `Enter` (write out / save)
   - `Ctrl + X` (exit)

4. Restart WSL to apply:
   ```powershell
   wsl --shutdown
   ```

5. Verify after reopening your distro:
   ```bash
   ls -l /dev/kvm
   groups
   ```

**Note:** If you have `systemd=true` set under `[boot]` in the same file,
`/etc/modules-load.d/modules.conf` will also work as an alternative — but
`[boot] command=` works regardless of whether systemd is enabled, and also
handles permissions in the same step.

---

## 8. Isolate the problem from Agent Framework (optional but recommended)

Before retrying the full CodeAct flow, test Hyperlight directly to confirm
the sandbox layer works on its own:

```bash
git clone https://github.com/hyperlight-dev/hyperlight.git
cd hyperlight
cargo run --example hello-world
```

- ✅ Success → your environment is fine; any remaining issue is specific to
  the `hyperlight-wasm` / Agent Framework setup (e.g. `HYPERLIGHT_PYTHON_GUEST_PATH`).
- ❌ Still fails → the environment issue (steps 1–7 above) isn't fully
  resolved yet.

---

## 9. Quick troubleshooting checklist

| Symptom | Likely cause | Fix |
|---|---|---|
| `vmx`/`svm` missing from `/proc/cpuinfo` | Nested virtualization not passed to WSL2 | Step 2, confirm Windows 11 |
| `/dev/kvm` missing, kernel is `5.15.x` | Kernel too old, no KVM module | Step 3 |
| `/dev/kvm` missing, kernel is `6.x` | Modules not loaded | Step 5 |
| `/dev/kvm` exists but "Permission denied" | Wrong ownership/group | Step 6 |
| `/dev/kvm` disappears after `wsl --shutdown` | Modules not set to auto-load | Step 7 |
| Native Windows (no WSL) VM creation failure | WHP not enabled, BIOS virtualization off, or conflicting hypervisor (VirtualBox/VMware) | Enable WHP via `Enable-WindowsOptionalFeature -Online -FeatureName HypervisorPlatform -All`, check BIOS, close conflicting hypervisors |

---

## 10. Related environment variable (Wasm backend)

The Hyperlight Wasm backend also requires:
```bash
export HYPERLIGHT_PYTHON_GUEST_PATH=/absolute/path/to/guest/module
```
set before running, pointing at the actual Hyperlight Python guest module
file (not just a directory).
