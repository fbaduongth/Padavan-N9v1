#!/usr/bin/env python3
"""
ConCard Enterprise Custom Firmware BSP & 802.11k/r Fast Roaming Installer
Target Device : TOTOLINK N9v1 (CaryStudio CSB334A, Rev 0154)
SoC / Memory  : MediaTek MT7620A (580MHz) / 128MB DDR2 / 8MB SPI NOR Flash
Radio Design  : 2.4GHz 2T2R 300Mbps + External PA & External LNA (Factory @ 0x40000)
"""

import os
import shutil
import sys

TRUNK = os.environ.get("TRUNK_ENV", "/opt/rt-n56u/trunk")
WIN_CUSTOM_DIR = os.path.dirname(os.path.abspath(__file__))
WIN_BSP_DIR = os.path.join(WIN_CUSTOM_DIR, "bsp")
BOARD_ID = "CSB334A-2700"
BOARD_DIR = os.path.join(TRUNK, "configs/boards", BOARD_ID)
TEMPLATE_PATH = os.path.join(TRUNK, "configs/templates", f"{BOARD_ID}.config")


def set_kconfig_line(text: str, symbol: str, val) -> str:
    """Set or disable a kernel config symbol cleanly."""
    lines = text.splitlines()
    out = []
    matched = False
    prefix_eq = f"{symbol}="
    prefix_unset = f"# {symbol} is not set"
    if val is None or val is False or val == "n":
        new_line = f"# {symbol} is not set"
    else:
        new_line = f"{symbol}={val}"

    for line in lines:
        if line.startswith(prefix_eq) or line == prefix_unset:
            if not matched:
                out.append(new_line)
                matched = True
        else:
            out.append(line)
    if not matched:
        out.append(new_line)
    return "\n".join(out) + "\n"


def build_kernel_config() -> str:
    oye_cfg_path = os.path.join(TRUNK, "configs/boards/OYE-001/kernel-3.4.x.config")
    with open(oye_cfg_path, "r", encoding="utf-8") as f:
        cfg = f.read()

    # 1. Exact 8MB SPI Flash layout matching stock TOTOLINK N9v1:
    #    0x000000..0x030000 Bootloader (192K)
    #    0x030000..0x040000 Config     (64K)
    #    0x040000..0x050000 Factory    (64K - RF EEPROM)
    #    0x050000..0x700000 Firmware   (6848K - Kernel + SquashFS RootFS)
    #    0x700000..0x800000 Storage    (1024K - /etc/storage, matches stock UserData)
    cfg = set_kconfig_line(cfg, "CONFIG_RT2880_FLASH_16M", None)
    cfg = set_kconfig_line(cfg, "CONFIG_RT2880_FLASH_8M", "y")
    cfg = set_kconfig_line(cfg, "CONFIG_MTD_STORE_PART_SIZ", "0x100000")

    # 2. Pinmux & External PA + External LNA RF Front-End (CRITICAL for N9v1 TX/RX power!)
    cfg = set_kconfig_line(cfg, "CONFIG_RALINK_GPIOMODE_PA_G", None)
    cfg = set_kconfig_line(cfg, "CONFIG_RALINK_GPIOMODE_EPHY", "y")
    cfg = set_kconfig_line(cfg, "CONFIG_RALINK_GPIOMODE_UARTF", "y")

    cfg = set_kconfig_line(cfg, "CONFIG_INTERNAL_PA_INTERNAL_LNA", None)
    cfg = set_kconfig_line(cfg, "CONFIG_INTERNAL_PA_EXTERNAL_LNA", None)
    cfg = set_kconfig_line(cfg, "CONFIG_EXTERNAL_PA_EXTERNAL_LNA", "y")
    cfg = set_kconfig_line(cfg, "CONFIG_RT2860V2_AP_RTMP_INTERNAL_TX_ALC", None)

    cfg = set_kconfig_line(cfg, "CONFIG_MT76X2_AP_INTERNAL_PA_INTERNAL_LNA", None)
    cfg = set_kconfig_line(cfg, "CONFIG_MT76X2_AP_INTERNAL_PA_EXTERNAL_LNA", None)
    cfg = set_kconfig_line(cfg, "CONFIG_MT76X2_AP_EXTERNAL_PA_EXTERNAL_LNA", "y")
    cfg = set_kconfig_line(cfg, "CONFIG_MT76X2_AP_RTMP_INTERNAL_TX_ALC", None)

    # 3. Enterprise High-Density Wi-Fi & Fast Roaming capabilities (+ strip unused ceiling-AP bloat)
    cfg = set_kconfig_line(cfg, "CONFIG_EXT4_FS", None)
    cfg = set_kconfig_line(cfg, "CONFIG_SOUND", None)
    cfg = set_kconfig_line(cfg, "CONFIG_MEDIA_SUPPORT", None)
    cfg = set_kconfig_line(cfg, "CONFIG_MMC", None)
    cfg = set_kconfig_line(cfg, "CONFIG_RT_MAX_CLIENTS", "64")
    cfg = set_kconfig_line(cfg, "CONFIG_RT_DOT11R_FT", "y")
    cfg = set_kconfig_line(cfg, "CONFIG_RT_DOT11K_RRM", "y")
    cfg = set_kconfig_line(cfg, "CONFIG_RT_ED_MONITOR", "y")
    cfg = set_kconfig_line(cfg, "CONFIG_RT_IGMP_SNOOP", "y")
    cfg = set_kconfig_line(cfg, "CONFIG_MT76X2_AP_MAC_REPEATER", None)
    cfg = set_kconfig_line(cfg, "CONFIG_MT76X2_AP_MWDS", None)

    # 4. Built-in FQ-CoDel & Packet Scheduler (zero-latency anti-bufferbloat)
    net_sched_block = """CONFIG_NET_SCHED=y

#
# Queueing/Scheduling
#
# CONFIG_NET_SCH_CBQ is not set
CONFIG_NET_SCH_HTB=m
CONFIG_NET_SCH_HFSC=m
CONFIG_NET_SCH_PRIO=m
# CONFIG_NET_SCH_MULTIQ is not set
CONFIG_NET_SCH_RED=m
# CONFIG_NET_SCH_SFB is not set
CONFIG_NET_SCH_SFQ=m
# CONFIG_NET_SCH_TEQL is not set
# CONFIG_NET_SCH_TBF is not set
CONFIG_NET_SCH_GRED=m
CONFIG_NET_SCH_DSMARK=m
# CONFIG_NET_SCH_NETEM is not set
# CONFIG_NET_SCH_DRR is not set
# CONFIG_NET_SCH_MQPRIO is not set
# CONFIG_NET_SCH_CHOKE is not set
# CONFIG_NET_SCH_QFQ is not set
# CONFIG_NET_SCH_INGRESS is not set
# CONFIG_NET_SCH_PLUG is not set
CONFIG_NET_SCH_CODEL=y
CONFIG_NET_SCH_FQ_CODEL=y

#
# Classification
#
CONFIG_NET_CLS=y
CONFIG_NET_CLS_BASIC=m
CONFIG_NET_CLS_TCINDEX=m
# CONFIG_NET_CLS_ROUTE4 is not set
CONFIG_NET_CLS_FW=m
CONFIG_NET_CLS_U32=m
# CONFIG_CLS_U32_PERF is not set
CONFIG_CLS_U32_MARK=y
# CONFIG_NET_CLS_RSVP is not set
# CONFIG_NET_CLS_RSVP6 is not set
CONFIG_NET_CLS_FLOW=m
CONFIG_NET_EMATCH=y
CONFIG_NET_EMATCH_STACK=32
CONFIG_NET_EMATCH_CMP=m
CONFIG_NET_EMATCH_NBYTE=m
CONFIG_NET_EMATCH_U32=m
CONFIG_NET_EMATCH_META=m
# CONFIG_NET_EMATCH_TEXT is not set
# CONFIG_NET_CLS_ACT is not set
# CONFIG_NET_CLS_IND is not set
CONFIG_NET_SCH_FIFO=y"""

    if "# CONFIG_NET_SCHED is not set" in cfg:
        cfg = cfg.replace("# CONFIG_NET_SCHED is not set", net_sched_block, 1)

    return cfg


def build_template_config() -> str:
    return """### Target Vendor/Product (support only Ralink RT3883/MT7620/MT7621/MT7628)
CONFIG_VENDOR=Ralink
CONFIG_PRODUCT=MT7620

### Target ProductID (board select, max 12 symbols - matches TOTOLINK CSB334A-<svn>)
CONFIG_FIRMWARE_PRODUCT_ID="CSB334A-2700"

### Linux kernel and toolchain
CONFIG_LINUXDIR=linux-3.4.x

############################################################
### Linux kernel configuration
############################################################
#CONFIG_FIRMWARE_TYPE_ROOTFS_IN_RAM=y
#CONFIG_FIRMWARE_CPU_600MHZ=y
#CONFIG_FIRMWARE_CPU_SLEEP=y

### Kernel driver select for WiFi AP 2.4GHz (3.0 = MT7620 v3.0.4.0 with 802.11k/r)
CONFIG_FIRMWARE_WIFI2_DRIVER=3.0

CONFIG_FIRMWARE_ENABLE_IPV6=y
CONFIG_FIRMWARE_ENABLE_USB=y
CONFIG_FIRMWARE_ENABLE_UFSD=n
CONFIG_FIRMWARE_INCLUDE_ANTFS=n
CONFIG_FIRMWARE_ENABLE_FAT=y
CONFIG_FIRMWARE_ENABLE_EXFAT=n
CONFIG_FIRMWARE_ENABLE_EXT2=n
CONFIG_FIRMWARE_ENABLE_EXT3=n
CONFIG_FIRMWARE_ENABLE_EXT4=n
CONFIG_FIRMWARE_ENABLE_XFS=n
CONFIG_FIRMWARE_ENABLE_FUSE=n
CONFIG_FIRMWARE_ENABLE_SWAP=n
CONFIG_FIRMWARE_INCLUDE_UVC=n
CONFIG_FIRMWARE_INCLUDE_HID=n
CONFIG_FIRMWARE_INCLUDE_SERIAL=n
CONFIG_FIRMWARE_INCLUDE_AUDIO=n
CONFIG_FIRMWARE_INCLUDE_QOS=y
CONFIG_FIRMWARE_INCLUDE_IMQ=n
CONFIG_FIRMWARE_INCLUDE_IFB=n
CONFIG_FIRMWARE_INCLUDE_IPSET=n
CONFIG_FIRMWARE_INCLUDE_NFSD=n
CONFIG_FIRMWARE_INCLUDE_NFSC=n
CONFIG_FIRMWARE_INCLUDE_CIFS=n

############################################################
### Userspace configuration (Lean Enterprise AP + Diagnostics)
############################################################
CONFIG_FIRMWARE_INCLUDE_LANG_CN=n
CONFIG_FIRMWARE_INCLUDE_NTFS_3G=n
CONFIG_FIRMWARE_INCLUDE_LPRD=n
CONFIG_FIRMWARE_INCLUDE_U2EC=n
CONFIG_FIRMWARE_INCLUDE_TCPDUMP=n
CONFIG_FIRMWARE_INCLUDE_HDPARM=n
CONFIG_FIRMWARE_INCLUDE_PARTED=n
CONFIG_FIRMWARE_INCLUDE_SMBD=n
CONFIG_FIRMWARE_INCLUDE_SMBD36=n
CONFIG_FIRMWARE_INCLUDE_WINS=n
CONFIG_FIRMWARE_INCLUDE_SMBD_SYSLOG=n
CONFIG_FIRMWARE_INCLUDE_FTPD=n
CONFIG_FIRMWARE_INCLUDE_RPL2TP=n
CONFIG_FIRMWARE_INCLUDE_EAP_PEAP=n
CONFIG_FIRMWARE_INCLUDE_HTTPS=y
CONFIG_FIRMWARE_INCLUDE_SFTP=n
CONFIG_FIRMWARE_INCLUDE_DROPBEAR=y
CONFIG_FIRMWARE_INCLUDE_DROPBEAR_FAST_CODE=y
CONFIG_FIRMWARE_INCLUDE_OPENSSH=n
CONFIG_FIRMWARE_INCLUDE_OPENVPN=n
CONFIG_FIRMWARE_INCLUDE_OPENSSL_EC=y
CONFIG_FIRMWARE_INCLUDE_OPENSSL_EXE=n
CONFIG_FIRMWARE_INCLUDE_XUPNPD=n
CONFIG_FIRMWARE_INCLUDE_MINIDLNA=n
CONFIG_FIRMWARE_INCLUDE_FIREFLY=n
CONFIG_FIRMWARE_INCLUDE_FFMPEG_NEW=n
CONFIG_FIRMWARE_INCLUDE_TRANSMISSION=n
CONFIG_FIRMWARE_INCLUDE_TRANSMISSION_WEB_CONTROL=n
CONFIG_FIRMWARE_INCLUDE_ARIA=n
CONFIG_FIRMWARE_INCLUDE_ARIA_WEB_CONTROL=n
CONFIG_FIRMWARE_INCLUDE_CURL=y
CONFIG_FIRMWARE_INCLUDE_SCUTCLIENT=n
CONFIG_FIRMWARE_INCLUDE_GDUT_DRCOM=n
CONFIG_FIRMWARE_INCLUDE_DOGCOM=n
CONFIG_FIRMWARE_INCLUDE_MINIEAP=n
CONFIG_FIRMWARE_INCLUDE_NJIT_CLIENT=n
CONFIG_FIRMWARE_INCLUDE_NAPT66=n
CONFIG_FIRMWARE_INCLUDE_SOFTETHERVPN_SERVER=n
CONFIG_FIRMWARE_INCLUDE_SOFTETHERVPN_CLIENT=n
CONFIG_FIRMWARE_INCLUDE_SOFTETHERVPN_CMD=n
CONFIG_FIRMWARE_INCLUDE_VLMCSD=n
CONFIG_FIRMWARE_INCLUDE_TTYD=y
CONFIG_FIRMWARE_INCLUDE_LRZSZ=n
CONFIG_FIRMWARE_INCLUDE_HTOP=y
CONFIG_FIRMWARE_INCLUDE_NANO=n
CONFIG_FIRMWARE_INCLUDE_IPERF3=y
CONFIG_FIRMWARE_INCLUDE_DUMP1090=n
CONFIG_FIRMWARE_INCLUDE_RTL_SDR=n
CONFIG_FIRMWARE_INCLUDE_MTR=y
CONFIG_FIRMWARE_INCLUDE_SOCAT=n
CONFIG_FIRMWARE_INCLUDE_SRELAY=n
CONFIG_FIRMWARE_INCLUDE_MENTOHUST=n
CONFIG_FIRMWARE_INCLUDE_FRPC=n
CONFIG_FIRMWARE_INCLUDE_FRPS=n
CONFIG_FIRMWARE_INCLUDE_TUNSAFE=n
CONFIG_FIRMWARE_INCLUDE_WIREGUARD=n
"""


def patch_ft_c():
    path = os.path.join(TRUNK, "proprietary/rt_wifi/rtpci/3.0.X.X/mt76x2/common/ft.c")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        txt = f.read()

    if "CONCARD_FT_PSK_LOCAL" in txt:
        print("[OK] ft.c already patched")
        return

    # 1. Fix FtR0khIdLen bug in FT_rtmp_read_parameters_from_file
    old_r0kh = (
        "\t\t\t\tNdisMoveMemory(pAd->ApCfg.MBSSID[Loop].FtCfg.FtR0khId, tmpbuf, strlen(tmpbuf));\n"
        "\t\t\t\tpAd->ApCfg.MBSSID[Loop].FtCfg.FtR0khId[strlen(tmpbuf)] = '\\0';"
    )
    new_r0kh = (
        "\t\t\t\tNdisZeroMemory(pAd->ApCfg.MBSSID[Loop].FtCfg.FtR0khId, sizeof(pAd->ApCfg.MBSSID[Loop].FtCfg.FtR0khId));\n"
        "\t\t\t\tNdisMoveMemory(pAd->ApCfg.MBSSID[Loop].FtCfg.FtR0khId, tmpbuf, strlen(tmpbuf));\n"
        "\t\t\t\tpAd->ApCfg.MBSSID[Loop].FtCfg.FtR0khId[strlen(tmpbuf)] = '\\0';\n"
        "\t\t\t\tpAd->ApCfg.MBSSID[Loop].FtCfg.FtR0khIdLen = strlen(tmpbuf);"
    )
    assert old_r0kh in txt, "ft.c: old_r0kh target not found"
    txt = txt.replace(old_r0kh, new_r0kh, 1)

    # 2. Add Controller-less IEEE 802.11r FT-PSK local PMK-R0 / PMK-R1 derivation
    old_auth = """\t\tif ((pR1hkEntry == NULL) ||
\t\t\t(RTMPEqualMemory(pEntry->FT_PMK_R1_NAME, pR1hkEntry->PmkR1Name, LEN_PMK_NAME) == FALSE))
\t\t{

\t\t\t/*\tIf the requested R0KH is not reachable, the AP shall respond 
\t\t\t\tto the Authentication Request with status code 28 ("R0KH unreachable"). */
\t\t\t{\t\t\t\t\t\t\t\t\t\t\t
\t\t\t\treturn FT_STATUS_CODE_R0KH_UNREACHABLE;
\t\t\t}
\t\t}"""

    new_auth = """\t\tif ((pR1hkEntry == NULL) ||
\t\t\t(RTMPEqualMemory(pEntry->FT_PMK_R1_NAME, pR1hkEntry->PmkR1Name, LEN_PMK_NAME) == FALSE))
\t\t{
\t\t\t/* CONCARD_FT_PSK_LOCAL: Controller-less IEEE 802.11r FT-PSK key derivation
\t\t\t * (equivalent to hostapd ft_psk_generate_local=1). When all APs share the
\t\t\t * same SSID, PSK, MDID, and R0KH-ID, PMK-R0 and PMK-R1 are deterministic. */
\t\t\tMULTISSID_STRUCT *pMbss = &pAd->ApCfg.MBSSID[pEntry->apidx];
\t\t\tif ((pMbss->wdev.AuthMode == Ndis802_11AuthModeWPA2PSK) ||
\t\t\t\t(pMbss->wdev.AuthMode == Ndis802_11AuthModeWPA1PSKWPA2PSK))
\t\t\t{
\t\t\t\tUINT8 localPmkR0[LEN_PMK];
\t\t\t\tUINT8 localPmkR0Name[LEN_PMK_NAME];
\t\t\t\tUINT8 localPmkR1[LEN_PMK];
\t\t\t\tUINT8 localPmkR1Name[LEN_PMK_NAME];
\t\t\t\tUINT8 localCount = 0;
\t\t\t\tPUINT8 localAkm = WPA_ExtractSuiteFromRSNIE(pFtInfo_in->RSN_IE, pFtInfo_in->RSNIE_Len, AKM_SUITE, &localCount);
\t\t\t\tPUINT8 localCipher = WPA_ExtractSuiteFromRSNIE(pFtInfo_in->RSN_IE, pFtInfo_in->RSNIE_Len, PAIRWISE_SUITE, &localCount);
\t\t\t\tUCHAR ftPskOUI[4] = {0x00, 0x0F, 0xAC, 0x04};

\t\t\t\tif (localAkm != NULL && localCipher != NULL &&
\t\t\t\t\tRTMPEqualMemory(localAkm, ftPskOUI, 4))
\t\t\t\t{
\t\t\t\t\tFT_DerivePMKR0(pMbss->PMK, LEN_PMK,
\t\t\t\t\t\t(PUINT8)pMbss->Ssid, pMbss->SsidLen,
\t\t\t\t\t\tpFtCfg->FtMdId,
\t\t\t\t\t\tpFtCfg->FtR0khId, pFtCfg->FtR0khIdLen,
\t\t\t\t\t\tpEntry->Addr,
\t\t\t\t\t\tlocalPmkR0, localPmkR0Name);

\t\t\t\t\tif (RTMPEqualMemory(pPmkR0Name, localPmkR0Name, LEN_PMK_NAME) == TRUE)
\t\t\t\t\t{
\t\t\t\t\t\tUINT32 keyLife = (pMbss->PMKCachePeriod > 0) ? (pMbss->PMKCachePeriod / OS_HZ) : 43200;
\t\t\t\t\t\tFT_DerivePMKR1(localPmkR0, localPmkR0Name,
\t\t\t\t\t\t\tpMbss->wdev.bssid, pEntry->Addr,
\t\t\t\t\t\t\tlocalPmkR1, localPmkR1Name);

\t\t\t\t\t\tif (pR1hkEntry != NULL)
\t\t\t\t\t\t\tFT_R1khEntryDelete(pAd, pR1hkEntry);

\t\t\t\t\t\tNdisMoveMemory(pEntry->FT_PMK_R0, localPmkR0, LEN_PMK);
\t\t\t\t\t\tNdisMoveMemory(pEntry->FT_PMK_R0_NAME, localPmkR0Name, LEN_PMK_NAME);
\t\t\t\t\t\tFT_R1khEntryInsert(pAd,
\t\t\t\t\t\t\tlocalPmkR0Name, localPmkR1Name, localPmkR1,
\t\t\t\t\t\t\tlocalCipher, localAkm,
\t\t\t\t\t\t\tkeyLife, 20,
\t\t\t\t\t\t\tpFtCfg->FtR0khId, pFtCfg->FtR0khIdLen,
\t\t\t\t\t\t\tpEntry->Addr);
\t\t\t\t\t\tpR1hkEntry = FT_R1khEntryTabLookup(pAd, pEntry->FT_PMK_R1_NAME);
\t\t\t\t\t}
\t\t\t\t}
\t\t\t}

\t\t\t/*\tIf the requested R0KH is still not reachable, respond with status code 28. */
\t\t\tif ((pR1hkEntry == NULL) ||
\t\t\t\t(RTMPEqualMemory(pEntry->FT_PMK_R1_NAME, pR1hkEntry->PmkR1Name, LEN_PMK_NAME) == FALSE))
\t\t\t{
\t\t\t\treturn FT_STATUS_CODE_R0KH_UNREACHABLE;
\t\t\t}
\t\t}"""

    assert old_auth in txt, "ft.c: old_auth target not found"
    txt = txt.replace(old_auth, new_auth, 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    print("[OK] Patched ft.c (FtR0khIdLen fix + CONCARD_FT_PSK_LOCAL)")


def patch_ralink_c():
    path = os.path.join(TRUNK, "user/rc/ralink.c")
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        txt = f.read()

    if "CONCARD_80211KR_CFG" in txt:
        print("[OK] ralink.c already patched")
        return

    old_rrm = '\tfprintf(fp, "RRMEnable=%d\\n", 0);\n\tfprintf(fp, "MboSupport=%d\\n", 0);'
    new_rrm = """\t/* CONCARD_80211KR_CFG: IEEE 802.11k RRM & IEEE 802.11r Fast BSS Transition */
\t{
\t\tint i_rrm = (nvram_wlan_get_int(is_aband, "rrm_enable") > 0) ? 1 : 0;
\t\tint i_ft_cfg = (nvram_wlan_get_int(is_aband, "ft_enable") > 0) ? 1 : 0;
\t\tconst char *s_auth = nvram_wlan_get(is_aband, "auth_mode");
\t\tconst char *s_crypto = nvram_wlan_get(is_aband, "crypto");
\t\tint i_wpa_m = nvram_wlan_get_int(is_aband, "wpa_mode");
\t\tint i_ft = (i_ft_cfg && !strcmp(s_auth, "psk") && i_wpa_m != 1 && strcmp(s_crypto, "tkip")) ? 1 : 0;
\t\tconst char *s_mdid = nvram_wlan_get(is_aband, "ft_mdid");
\t\tconst char *s_r0kh = nvram_wlan_get(is_aband, "ft_r0kh_id");
\t\tif (!s_mdid || strlen(s_mdid) != 2)
\t\t\ts_mdid = "CC";
\t\tif (!s_r0kh || strlen(s_r0kh) < 1 || strlen(s_r0kh) > 48)
\t\t\ts_r0kh = "ConCardFT";

\t\tfprintf(fp, "RRMEnable=%d;%d\\n", i_rrm, i_rrm);
\t\tif (!is_aband)
\t\t\tfprintf(fp, "RegulatoryClass=%d;%d\\n", 81, 81);
\t\tfprintf(fp, "FtSupport=%d;0\\n", i_ft);
\t\tfprintf(fp, "FtRic=%d;0\\n", i_ft);
\t\tfprintf(fp, "FtOtd=0;0\\n");
\t\tfprintf(fp, "FtMdId1=%s\\n", s_mdid);
\t\tfprintf(fp, "FtMdId2=%s\\n", s_mdid);
\t\tfprintf(fp, "FtR0khId1=%s\\n", s_r0kh);
\t\tfprintf(fp, "FtR0khId2=%s\\n", s_r0kh);
\t}
\tfprintf(fp, "MboSupport=%d\\n", 0);"""

    assert old_rrm in txt, "ralink.c: old_rrm target not found"
    txt = txt.replace(old_rrm, new_rrm, 1)

    old_pmk = '\tfprintf(fp, "PMKCachePeriod=%d\\n", 10);'
    new_pmk = '\tfprintf(fp, "PMKCachePeriod=%d\\n", (nvram_wlan_get_int(is_aband, "ft_enable") > 0) ? 720 : 10);'
    assert old_pmk in txt, "ralink.c: old_pmk target not found"
    txt = txt.replace(old_pmk, new_pmk, 1)

    with open(path, "w", encoding="utf-8") as f:
        f.write(txt)
    print("[OK] Patched user/rc/ralink.c (802.11k/r + 12h PMKCachePeriod)")


def patch_defaults():
    dh_path = os.path.join(TRUNK, "user/shared/defaults.h")
    with open(dh_path, "r", encoding="utf-8", errors="replace") as f:
        dh = f.read()

    if "BOARD_N9V1" not in dh:
        old_blk = """#define DEF_LAN_ADDR\t\t"192.168.2.1"
#define DEF_LAN_DHCP_BEG\t"192.168.2.100"
#define DEF_LAN_DHCP_END\t"192.168.2.244"
#define DEF_LAN_MASK\t\t"255.255.255.0"

#define DEF_WLAN_2G_CC\t\t"CN"
#define DEF_WLAN_5G_CC\t\t"US"
#define DEF_WLAN_2G_SSID\tBOARD_PID "_%s"
#define DEF_WLAN_5G_SSID\tBOARD_PID "_5G_%s"
#define DEF_WLAN_2G_GSSID\tBOARD_PID "_GUEST_%s"
#define DEF_WLAN_5G_GSSID\tBOARD_PID "_GUEST_5G_%s"
#define DEF_WLAN_2G_PSK\t\t"1234567890"
#define DEF_WLAN_5G_PSK\t\t"1234567890"

#define DEF_ROOT_PASSWORD\t"admin"
#define DEF_SMB_WORKGROUP\t"WORKGROUP"
#define DEF_TIMEZONE\t\t"CST-8"
#define DEF_NTP_SERVER0\t\t"ntp1.aliyun.com\""""

        new_blk = """#ifdef BOARD_N9V1
#define DEF_LAN_ADDR\t\t"192.168.1.165"
#define DEF_LAN_DHCP_BEG\t"192.168.1.100"
#define DEF_LAN_DHCP_END\t"192.168.1.244"
#define DEF_LAN_MASK\t\t"255.255.255.0"

#define DEF_WLAN_2G_CC\t\t"GB"
#define DEF_WLAN_5G_CC\t\t"US"
#define DEF_WLAN_2G_SSID\t"ConCard-N9_%s"
#define DEF_WLAN_5G_SSID\t"ConCard-N9_5G_%s"
#define DEF_WLAN_2G_GSSID\t"ConCard-Guest_%s"
#define DEF_WLAN_5G_GSSID\t"ConCard-Guest_5G_%s"
#define DEF_WLAN_2G_PSK\t\t"1234567890"
#define DEF_WLAN_5G_PSK\t\t"1234567890"

#define DEF_ROOT_PASSWORD\t"admin"
#define DEF_SMB_WORKGROUP\t"WORKGROUP"
#define DEF_TIMEZONE\t\t"CST-7"
#define DEF_NTP_SERVER0\t\t"time.google.com"
#else
#define DEF_LAN_ADDR\t\t"192.168.2.1"
#define DEF_LAN_DHCP_BEG\t"192.168.2.100"
#define DEF_LAN_DHCP_END\t"192.168.2.244"
#define DEF_LAN_MASK\t\t"255.255.255.0"

#define DEF_WLAN_2G_CC\t\t"CN"
#define DEF_WLAN_5G_CC\t\t"US"
#define DEF_WLAN_2G_SSID\tBOARD_PID "_%s"
#define DEF_WLAN_5G_SSID\tBOARD_PID "_5G_%s"
#define DEF_WLAN_2G_GSSID\tBOARD_PID "_GUEST_%s"
#define DEF_WLAN_5G_GSSID\tBOARD_PID "_GUEST_5G_%s"
#define DEF_WLAN_2G_PSK\t\t"1234567890"
#define DEF_WLAN_5G_PSK\t\t"1234567890"

#define DEF_ROOT_PASSWORD\t"admin"
#define DEF_SMB_WORKGROUP\t"WORKGROUP"
#define DEF_TIMEZONE\t\t"CST-8"
#define DEF_NTP_SERVER0\t\t"ntp1.aliyun.com"
#endif"""
        assert old_blk in dh, "defaults.h: target block not found"
        dh = dh.replace(old_blk, new_blk, 1)
        with open(dh_path, "w", encoding="utf-8") as f:
            f.write(dh)
        print("[OK] Patched user/shared/defaults.h")
    else:
        print("[OK] defaults.h already patched")

    dc_path = os.path.join(TRUNK, "user/shared/defaults.c")
    with open(dc_path, "r", encoding="utf-8", errors="replace") as f:
        dc = f.read()

    if "rt_ft_enable" not in dc:
        # STP off on N9v1 pure AP to avoid 30s bridge forwarding delay
        old_stp = '\t{ "lan_stp", "1" },\t\t\t/* LAN spanning tree protocol */'
        new_stp = (
            "#ifdef BOARD_N9V1\n"
            '\t{ "lan_stp", "0" },\t\t\t/* Instant bridge forwarding on pure AP */\n'
            "#else\n"
            '\t{ "lan_stp", "1" },\t\t\t/* LAN spanning tree protocol */\n'
            "#endif"
        )
        assert old_stp in dc, "defaults.c: old_stp not found"
        dc = dc.replace(old_stp, new_stp, 1)

        # High-density 20MHz bandwidth default on N9v1
        old_bw = '\t{ "rt_HT_BW", "1" },'
        new_bw = (
            "#ifdef BOARD_N9V1\n"
            '\t{ "rt_HT_BW", "0" },\t\t\t/* 20MHz high-density enterprise channel width */\n'
            "#else\n"
            '\t{ "rt_HT_BW", "1" },\n'
            "#endif"
        )
        assert old_bw in dc, "defaults.c: old_bw not found"
        dc = dc.replace(old_bw, new_bw, 1)

        # AMSDU + Active RSSI Roaming Assistant + 802.11k/r FT-PSK defaults
        old_rssi = (
            '\t{ "rt_HT_AMSDU", "0" },\n'
            '\t{ "rt_HT_MpduDensity", "5" },'
        )
        new_rssi_amsdu = (
            "#ifdef BOARD_N9V1\n"
            '\t{ "rt_HT_AMSDU", "1" },\n'
            "#else\n"
            '\t{ "rt_HT_AMSDU", "0" },\n'
            "#endif\n"
            '\t{ "rt_HT_MpduDensity", "5" },'
        )
        assert old_rssi in dc, "defaults.c: old_rssi_amsdu not found"
        dc = dc.replace(old_rssi, new_rssi_amsdu, 1)

        old_kick = (
            '\t{ "rt_KickStaRssiLow", "0" },\n'
            '\t{ "rt_AssocReqRssiThres", "0" },'
        )
        new_kick = (
            "#ifdef BOARD_N9V1\n"
            '\t{ "rt_KickStaRssiLow", "-78" },\n'
            '\t{ "rt_AssocReqRssiThres", "-82" },\n'
            '\t{ "rt_rrm_enable", "1" },\n'
            '\t{ "rt_ft_enable", "1" },\n'
            '\t{ "rt_ft_mdid", "CC" },\n'
            '\t{ "rt_ft_r0kh_id", "ConCardFT" },\n'
            "#else\n"
            '\t{ "rt_KickStaRssiLow", "0" },\n'
            '\t{ "rt_AssocReqRssiThres", "0" },\n'
            '\t{ "rt_rrm_enable", "0" },\n'
            '\t{ "rt_ft_enable", "0" },\n'
            '\t{ "rt_ft_mdid", "CC" },\n'
            '\t{ "rt_ft_r0kh_id", "ConCardFT" },\n'
            "#endif"
        )
        assert old_kick in dc, "defaults.c: old_kick not found"
        dc = dc.replace(old_kick, new_kick, 1)

        with open(dc_path, "w", encoding="utf-8") as f:
            f.write(dc)
        print("[OK] Patched user/shared/defaults.c")
    else:
        print("[OK] defaults.c already patched")


def patch_webui():
    var_path = os.path.join(TRUNK, "user/httpd/variables.c")
    with open(var_path, "r", encoding="utf-8", errors="replace") as f:
        vtxt = f.read()

    if "rt_ft_enable" not in vtxt:
        old_v = (
            '\t\t\t{"rt_KickStaRssiLow", "", NULL, EVM_RESTART_WIFI2},\n'
            '\t\t\t{"rt_AssocReqRssiThres", "", NULL, EVM_RESTART_WIFI2},'
        )
        new_v = (
            '\t\t\t{"rt_KickStaRssiLow", "", NULL, EVM_RESTART_WIFI2},\n'
            '\t\t\t{"rt_AssocReqRssiThres", "", NULL, EVM_RESTART_WIFI2},\n'
            '\t\t\t{"rt_rrm_enable", "", NULL, EVM_RESTART_WIFI2},\n'
            '\t\t\t{"rt_ft_enable", "", NULL, EVM_RESTART_WIFI2},\n'
            '\t\t\t{"rt_ft_mdid", "", NULL, EVM_RESTART_WIFI2},\n'
            '\t\t\t{"rt_ft_r0kh_id", "", NULL, EVM_RESTART_WIFI2},'
        )
        assert old_v in vtxt, "variables.c: target not found"
        vtxt = vtxt.replace(old_v, new_v, 1)
        with open(var_path, "w", encoding="utf-8") as f:
            f.write(vtxt)
        print("[OK] Patched user/httpd/variables.c")
    else:
        print("[OK] variables.c already patched")

    asp_path = os.path.join(TRUNK, "user/www/n56u_ribbon_fixed/Advanced_Wireless2g_Content.asp")
    with open(asp_path, "r", encoding="utf-8", errors="replace") as f:
        atxt = f.read()

    if "rt_ft_enable" not in atxt:
        old_asp = """                                        <tr>
                                            <th><a class="help_tooltip" href="javascript:void(0);" onmouseover="openTooltip(this, 0, 26);"><#WLANConfig11b_AssocReqRssiThres_itemname#></a></th>
                                            <td>
                                                <input type="text" maxlength="4" size="4" name="rt_AssocReqRssiThres" class="input" value="<% nvram_get_x("", "rt_AssocReqRssiThres"); %>" />
                                                &nbsp;<span style="color:#888;">[-100..0]</span>
                                            </td>
                                        </tr>"""

        new_asp = old_asp + """
                                        <tr>
                                            <th>802.11k Neighbor Report (RRM)</th>
                                            <td>
                                                <select name="rt_rrm_enable" class="input">
                                                    <option value="0" <% nvram_match_x("", "rt_rrm_enable", "0", "selected"); %>>Disable</option>
                                                    <option value="1" <% nvram_match_x("", "rt_rrm_enable", "1", "selected"); %>>Enable (*)</option>
                                                </select>
                                            </td>
                                        </tr>
                                        <tr>
                                            <th>802.11r Fast Roaming (FT-PSK)</th>
                                            <td>
                                                <select name="rt_ft_enable" class="input">
                                                    <option value="0" <% nvram_match_x("", "rt_ft_enable", "0", "selected"); %>>Disable</option>
                                                    <option value="1" <% nvram_match_x("", "rt_ft_enable", "1", "selected"); %>>Enable (Hybrid WPA2+FT *)</option>
                                                </select>
                                            </td>
                                        </tr>
                                        <tr>
                                            <th>802.11r Mobility Domain ID</th>
                                            <td>
                                                <input type="text" maxlength="2" size="4" name="rt_ft_mdid" class="input" value="<% nvram_get_x("", "rt_ft_mdid"); %>" />
                                                &nbsp;<span style="color:#888;">[2 chars, e.g. CC]</span>
                                            </td>
                                        </tr>"""
        assert old_asp in atxt, "Advanced_Wireless2g_Content.asp: target not found"
        atxt = atxt.replace(old_asp, new_asp, 1)
        with open(asp_path, "w", encoding="utf-8") as f:
            f.write(atxt)
        print("[OK] Patched Advanced_Wireless2g_Content.asp")
    else:
        print("[OK] Advanced_Wireless2g_Content.asp already patched")


def patch_mtd_storage():
    sh_path = os.path.join(TRUNK, "user/scripts/mtd_storage.sh")
    with open(sh_path, "r", encoding="utf-8", errors="replace") as f:
        stxt = f.read()

    if "ConCard Enterprise AP Tuning" not in stxt:
        old_s = """#drop caches
sync && echo 3 > /proc/sys/vm/drop_caches"""

        new_s = """# ConCard Enterprise AP Tuning: High Conntrack + FQ-CoDel Anti-Bufferbloat
sysctl -w net.netfilter.nf_conntrack_max=32768 >/dev/null 2>&1
tc qdisc replace dev eth2 root fq_codel quantum 300 limit 1024 noecn >/dev/null 2>&1
tc qdisc replace dev ra0 root fq_codel quantum 300 limit 1024 noecn >/dev/null 2>&1

#drop caches
sync && echo 3 > /proc/sys/vm/drop_caches"""

        assert old_s in stxt, "mtd_storage.sh: target not found"
        stxt = stxt.replace(old_s, new_s, 1)
        with open(sh_path, "w", encoding="utf-8") as f:
            f.write(stxt)
        print("[OK] Patched user/scripts/mtd_storage.sh (FQ-CoDel + nf_conntrack_max=32768)")
    else:
        print("[OK] mtd_storage.sh already patched")


def patch_dropbear_harden():
    db_path = os.path.join(TRUNK, "user/dropbear/Makefile")
    with open(db_path, "r", encoding="utf-8", errors="replace") as f:
        dtxt = f.read()
    if "--disable-harden" not in dtxt:
        dtxt = dtxt.replace("--enable-zlib \\", "--disable-harden \\\n\t\t--enable-zlib \\", 1)
        with open(db_path, "w", encoding="utf-8") as f:
            f.write(dtxt)
        print("[OK] Patched user/dropbear/Makefile (--disable-harden for uClibc)")
    else:
        print("[OK] user/dropbear/Makefile already patched")


def patch_stock_rollback_support():
    up_path = os.path.join(TRUNK, "user/httpd/upload.c")
    with open(up_path, "r", encoding="utf-8", errors="replace") as f:
        utxt = f.read()
    if 'strncmp(buf + 32, "CSB334A-", 8)' not in utxt:
        old_u = "\tif (strcmp(pid_asus, BOARD_PID) != 0) {"
        new_u = '\tif (strcmp(pid_asus, BOARD_PID) != 0 && strncmp(buf + 32, "CSB334A-", 8) != 0) {'
        assert old_u in utxt, "upload.c: BOARD_PID check not found"
        utxt = utxt.replace(old_u, new_u, 1)
        with open(up_path, "w", encoding="utf-8") as f:
            f.write(utxt)
        print("[OK] Patched user/httpd/upload.c (accept Stock TOTOLINK CSB334A-* Web UI rollback)")
    else:
        print("[OK] user/httpd/upload.c already patched")

    rc_path = os.path.join(TRUNK, "user/rc/rc.c")
    with open(rc_path, "r", encoding="utf-8", errors="replace") as f:
        rtxt = f.read()
    if "CONCARD_STOCK_ROLLBACK_CLEAN_CFG" not in rtxt:
        old_r = '\tif (eval("/tmp/mtd_write", "-r", "write", FW_IMG_NAME, FW_MTD_NAME) != 0) {'
        new_r = (
            "\t/* CONCARD_STOCK_ROLLBACK_CLEAN_CFG: erase Config NVRAM when rolling back to Stock CSB334A */\n"
            "\t{\n"
            "\t\tFILE *fp_fw = fopen(FW_IMG_NAME, \"rb\");\n"
            "\t\tif (fp_fw) {\n"
            "\t\t\tchar fw_hdr[64] = {0};\n"
            "\t\t\tif (fread(fw_hdr, 1, sizeof(fw_hdr), fp_fw) == sizeof(fw_hdr) &&\n"
            "\t\t\t    strncmp(fw_hdr + 32, \"CSB334A-\", 8) == 0) {\n"
            "\t\t\t\tfclose(fp_fw);\n"
            "\t\t\t\tfp_fw = NULL;\n"
            "\t\t\t\teval(\"/tmp/mtd_write\", \"erase\", \"Config\");\n"
            "\t\t\t}\n"
            "\t\t\tif (fp_fw)\n"
            "\t\t\t\tfclose(fp_fw);\n"
            "\t\t}\n"
            "\t}\n"
            '\tif (eval("/tmp/mtd_write", "-r", "write", FW_IMG_NAME, FW_MTD_NAME) != 0) {'
        )
        assert old_r in rtxt, "rc.c: mtd_write target not found"
        rtxt = rtxt.replace(old_r, new_r, 1)
        with open(rc_path, "w", encoding="utf-8") as f:
            f.write(rtxt)
        print("[OK] Patched user/rc/rc.c (auto-clean Config on Stock CSB334A rollback)")
    else:
        print("[OK] user/rc/rc.c already patched")


def patch_depmod_sh():
    dm_path = os.path.join(TRUNK, "tools/depmod.sh")
    with open(dm_path, "r", encoding="utf-8", errors="replace") as f:
        dm = f.read()
    changed = False
    old_call = '$depmod_bin -ae -F System.map -b "${INSTALL_MOD_PATH}" -r ${KERNELRELEASE}'
    new_call = '$depmod_bin -ae -F System.map -b "${INSTALL_MOD_PATH}" ${KERNELRELEASE}'
    if old_call in dm:
        dm = dm.replace(old_call, new_call, 1)
        changed = True
    if "modules.weakdep" not in dm:
        dm = dm.rstrip() + '\nrm -f "${INSTALL_MOD_PATH}/lib/modules/${KERNELRELEASE}/modules.weakdep"\n'
        changed = True
    if changed:
        with open(dm_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(dm)
        print("[OK] Patched tools/depmod.sh (modern kmod compatibility without -r flag)")
    else:
        print("[OK] tools/depmod.sh already patched")


def main():
    os.makedirs(BOARD_DIR, exist_ok=True)
    os.makedirs(WIN_BSP_DIR, exist_ok=True)

    # Copy board.h & board.mk
    shutil.copyfile(os.path.join(WIN_BSP_DIR, "board.h"), os.path.join(BOARD_DIR, "board.h"))
    shutil.copyfile(os.path.join(WIN_BSP_DIR, "board.mk"), os.path.join(BOARD_DIR, "board.mk"))
    print(f"[OK] Installed board.h & board.mk -> {BOARD_DIR}")

    # Generate kernel-3.4.x.config
    kcfg = build_kernel_config()
    with open(os.path.join(BOARD_DIR, "kernel-3.4.x.config"), "w", encoding="utf-8", newline="\n") as f:
        f.write(kcfg)
    with open(os.path.join(WIN_BSP_DIR, "kernel-3.4.x.config"), "w", encoding="utf-8", newline="\n") as f:
        f.write(kcfg)
    print(f"[OK] Generated kernel-3.4.x.config ({len(kcfg.splitlines())} lines)")

    # Generate CSB334A-2700.config template
    tcfg = build_template_config()
    with open(TEMPLATE_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write(tcfg)
    with open(os.path.join(WIN_BSP_DIR, f"{BOARD_ID}.config"), "w", encoding="utf-8", newline="\n") as f:
        f.write(tcfg)
    print(f"[OK] Generated {TEMPLATE_PATH}")

    # Apply source patches
    patch_ft_c()
    patch_ralink_c()
    patch_defaults()
    patch_webui()
    patch_mtd_storage()
    patch_dropbear_harden()
    patch_stock_rollback_support()
    patch_depmod_sh()
    print("=== ALL CONCARD N9V1 (CSB334A-2700) BSP & 802.11k/r PATCHES APPLIED SUCCESSFULLY ===")


if __name__ == "__main__":
    main()
