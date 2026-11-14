#!/usr/bin/env bash
# ==============================================================================
# ConCard Custom Firmware Automated Builder for TOTOLINK N9v1 (CSB334A-2700)
# Target: MediaTek MT7620A (580MHz) / 128MB DDR2 / 8MB SPI NOR Flash
# Base  : Padavan rt-n56u (Linux 3.4.113 + MediaTek mt76x2_ap v3.0.5.0)
# ==============================================================================
set -euo pipefail

export PATH="/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
export CMAKE_POLICY_VERSION_MINIMUM=3.5

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RT_N56U_ROOT="${RT_N56U_ROOT:-/opt/rt-n56u}"
TRUNK_DIR="${RT_N56U_ROOT}/trunk"

echo "[1/4] Checking Padavan source tree & MIPS toolchain at ${RT_N56U_ROOT}..."
if [ ! -d "${TRUNK_DIR}" ]; then
  echo "Cloning hanwckf/rt-n56u into ${RT_N56U_ROOT}..."
  git clone --depth=1 https://github.com/hanwckf/rt-n56u.git "${RT_N56U_ROOT}"
fi

if [ ! -d "${RT_N56U_ROOT}/toolchain-mipsel/toolchain-3.4.x/bin" ]; then
  echo "ERROR: MIPS toolchain not found at ${RT_N56U_ROOT}/toolchain-mipsel/toolchain-3.4.x"
  echo "Build or extract the Padavan mipsel-linux-uclibc toolchain first (dl_toolchain.sh)."
  exit 1
fi

echo "[2/4] Applying ConCard N9v1 (CSB334A-2700) BSP & 802.11k/r patches..."
TRUNK_ENV="${TRUNK_DIR}" python3 "${SCRIPT_DIR}/apply_concard_n9v1_bsp.py"

echo "[3/4] Compiling Kernel 3.4.113, mt76x2_ap (64 clients + 802.11k/r), and Userspace..."
cd "${TRUNK_DIR}"
./build_firmware_modify CSB334A-2700

echo "[4/4] Verifying modules.dep & copying output images..."
test -s "${TRUNK_DIR}/romfs/lib/modules/3.4.113/modules.dep"
grep -q "mt76x2_ap.ko:" "${TRUNK_DIR}/romfs/lib/modules/3.4.113/modules.dep"

TRX_FILE="$(ls -1 "${TRUNK_DIR}"/images/CSB334A-2700*.trx | head -n 1)"
cp -f "${TRX_FILE}" "${SCRIPT_DIR}/ConCard_Padavan_N9v1_CSB334A-2700_v1.0.trx"
cp -f "${TRX_FILE}" "${SCRIPT_DIR}/ConCard_Padavan_N9v1_CSB334A-2700_v1.0.web"
ls -lh "${SCRIPT_DIR}"/ConCard_Padavan_N9v1_CSB334A-2700_v1.0.*
echo "=== BUILD COMPLETE ==="
