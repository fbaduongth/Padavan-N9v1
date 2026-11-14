<div align="center">
  <h1>Padavan-N9v1 — Custom Enterprise Firmware cho TOTOLINK N9v1</h1>
  <p><b>Bản độ Padavan Linux 3.4.113 chuyên dụng cho Access Point ốp trần TOTOLINK N9v1 (<code>CSB334A</code>): Mở khóa 64 Clients, Fast Roaming <code>802.11k/r</code> (<code>FT-PSK</code> không cần Controller), chống nghẽn <code>FQ-CoDel</code> &amp; Rollback 1-Click về Stock</b></p>
  <p>
    <img src="https://img.shields.io/badge/Version-v1.0.0-2563eb?style=flat-square" alt="Version v1.0.0" />
    <img src="https://img.shields.io/badge/Target-TOTOLINK%20N9v1%20(CSB334A)-0284c7?style=flat-square" alt="Target Hardware" />
    <img src="https://img.shields.io/badge/SoC-MT7620A%20%7C%20128MB%20RAM%20%7C%208MB%20SPI-0f172a?style=flat-square" alt="SoC" />
    <img src="https://img.shields.io/badge/Wi--Fi-mt76x2__ap%20v3.0.5.0%20(802.11k%2Fr)-16a34a?style=flat-square" alt="Wi-Fi Driver" />
    <img src="https://img.shields.io/badge/License-GPL--2.0-d97706?style=flat-square" alt="License" />
  </p>
</div>

---

## 1. Giới Thiệu & Động Lực Phát Triển

**TOTOLINK N9v1** (bo mạch OEM **CaryStudio `CSB334A` Rev 0154**) sở hữu phần cứng rất tốt trong phân khúc Access Point `2.4 GHz` ốp trần PoE: SoC **MediaTek MT7620A `580 MHz`**, bộ nhớ **RAM `128 MB DDR2`** (gấp đôi hầu hết các AP cùng tầm giá) và mạch khuếch đại công suất rời **External PA + External LNA** (`2T2R 300 Mbps`).

Tuy nhiên, bản **Stock Firmware `V4.0c.2634` (Linux 2.6.36 cũ)** của hãng bó hẹp nghiêm trọng năng lực phần cứng khi triển khai mật độ cao tại khách sạn, tòa nhà, trường học:
- Khóa cứng bảng MAC ở mức **`32` clients/AP** ngay trong driver.
- **Không hỗ trợ `802.11k` / `802.11r`**, khiến điện thoại/laptop bị đứt kết nối `500–2500 ms` mỗi khi di chuyển dọc hành lang.
- Hàng đợi gói tin FIFO cổ điển gây vọt ping (`Bufferbloat > 300 ms`) khi có người tải nặng, và bảng `nf_conntrack` nhỏ dễ đầy.

**Padavan-N9v1 (`CSB334A-2700`)** giải quyết triệt để các giới hạn trên mà **không cần tháo vỏ hàn dây UART hay kẹp chip SPI**: nạp trực tiếp file `.web` ngay từ giao diện Web của TOTOLINK Stock và hỗ trợ **Rollback 1-Click** quay lại Firmware gốc của hãng bất kỳ lúc nào.

---

## 2. Bảng So Sánh Kỹ Thuật: Stock `V4.0c.2634` vs `Padavan-N9v1 v1.0`

| Hạng mục | Stock TOTOLINK `V4.0c.2634` | `Padavan-N9v1` (`CSB334A-2700` v1.0) |
| :--- | :--- | :--- |
| **Nhân hệ điều hành & Driver Wi-Fi** | Linux `2.6.36` + `rt2860v2_ap` cũ | **Linux `3.4.113` + MediaTek `mt76x2_ap` `v3.0.5.0`** |
| **Giới hạn Client Wi-Fi (`MAX_CLIENTS`)** | `32` clients cứng | **`64` clients** (`CONFIG_RT_MAX_CLIENTS=64`) |
| **Fast BSS Transition `802.11r` (`FT-PSK`)** | Không có | **Hybrid `WPA2-PSK + FT-PSK` (`< 30 ms`)**, tự dẫn xuất khóa cục bộ `PMK-R0/R1` (`CONCARD_FT_PSK_LOCAL`) **không cần Controller** |
| **Neighbor Report `802.11k` (`RRM`)** | Không có | **Bật sẵn (`RRMEnable=1`, Regulatory Class `81`)** |
| **Active Roaming Steering (chống bám sóng yếu)** | Thiếu ổn định | **Bật sẵn `KickStaRssiLow=-78 dBm` & `AssocReqRssiThres=-82 dBm`** (tùy chỉnh trực tiếp trên Web UI) |
| **Loại bỏ tốc độ cổ `802.11b` gây nghẽn sóng** | Phát beacon `1 / 2 Mbps` gây chiếm dụng airtime | **`Basic rates: 6 / 12 / 24 Mbps` (`OFDM + HT 20 MHz`)** |
| **Chống nghẽn hàng đợi (`Anti-Bufferbloat`)** | FIFO truyền thống | **Kernel `FQ-CoDel` (`quantum 300`, `limit 1024p`, `target 5ms`, `noecn`)** gắn tự động trên cả `eth2` và `ra0` |
| **Bảng Conntrack & Mức tiêu thụ RAM** | Conntrack `4,096` | **`nf_conntrack_max = 32,768`** • Chỉ tiêu thụ **`~11.6 MB RAM`**, còn trống **`~112.1 MB RAM`**! |
| **Tương thích mạch khuếch đại RF N9v1** | External PA + External LNA | **`CONFIG_MT76X2_AP_EXTERNAL_PA_EXTERNAL_LNA=y`**, giữ nguyên phân vùng hiệu chuẩn `Factory` (`0x40000`) |
| **Công cụ chẩn đoán tích hợp sẵn** | Không có | **`iperf3`, `mtr`, `htop`, `curl`, `ttyd` (Web Terminal), Dropbear SSH** |
| **Quay về Firmware gốc (Rollback)** | — | **Hỗ trợ nạp ngược file `.web` gốc của TOTOLINK trực tiếp trên Web UI** (tự động xóa sạch `Config` NVRAM trước khi ghi) |

---

## 3. Sơ Đồ Phân Vùng SPI NOR Flash (`8 MB` — Khớp 100% Bootloader Gốc)

```text
0x000000 ──┬──────────────────────────────┬── mtd0: Bootloader (192 KB)  [Giữ nguyên tuyệt đối]
0x030000 ──┼──────────────────────────────┼── mtd1: Config     (64 KB)   [NVRAM cấu hình]
0x040000 ──┼──────────────────────────────┼── mtd2: Factory    (64 KB)   [MAC & RF Calibration EEPROM - Giữ nguyên]
0x050000 ──┼──────────────────────────────┼── mtd3+mtd4: Firmware (6,848 KB = 7,012,352 B tối đa)
           │  Kernel LZMA  (~1.10 MiB)    │   -> Ảnh Padavan-N9v1 chỉ chiếm 5.69 MiB (5,963,587 B)
           │  RootFS XZ    (~4.58 MiB)    │   -> Còn trống > 1,024 KB dự phòng an toàn!
0x700000 ──┼──────────────────────────────┼── mtd5: Storage    (1,024 KB)[/etc/storage bền vững qua mỗi lần nâng cấp]
0x800000 ──┴──────────────────────────────┴── Kết thúc chip Flash EN25QH64 (8 MB)
```

---

## 4. Thông Số Mặc Định Sau Khi Nạp

- **Chế độ vận hành mặc định:** **Pure Access Point Bridge (`sw_mode=3`)** — toàn bộ 5 cổng switch (`ESW LLLLL`) và Wi-Fi `ra0` đều gộp chung vào cầu nối `br0` (`STP off`, `IGMP snooping on`).
- **Địa chỉ IP quản trị:**
  - **Cắm vào mạng LAN có DHCP Server/Router:** Tự động nhận IP qua **DHCP Client** (hostname `TOTOLINK-N9V1`), chống xung đột IP tuyệt đối khi cắm hàng loạt AP cùng lúc.
  - **Cắm dây LAN trực tiếp vào PC (không có DHCP):** Tự động fallback về IP tĩnh **`192.168.1.165`** (`255.255.255.0`).
- **Tài khoản quản trị Web UI & SSH mặc định:** `admin` / `admin`
- **Wi-Fi `2.4 GHz` mặc định:**
  - **SSID:** `ConCard-N9_XXXX` (4 ký tự cuối địa chỉ MAC của AP)
  - **Mật khẩu:** `1234567890` (`WPA2-Personal AES/CCMP` + `Hybrid 802.11r FT-PSK` + `802.11k RRM` bật sẵn)
  - **Độ rộng kênh:** `20 MHz` (tự động quét phổ CCA chọn kênh sạch nhất khi khởi động)
- **Nút cứng Reset (`GPIO 13`) & Đèn LED trần (`GPIO 11` Xanh / `GPIO 39` Đỏ):** Nhấn giữ nút Reset `> 5 giây` để khôi phục cấu hình gốc bất kỳ lúc nào.

---

## 5. Hướng Dẫn Nạp Firmware Từ Giao Diện TOTOLINK Stock (Không Cần UART)

1. Tải file **`ConCard_Padavan_N9v1_CSB334A-2700_v1.0.web`** tại mục **[Releases](https://github.com/fbaduongth/Padavan-N9v1/releases)** (hoặc ngay trong thư mục [`releases/`](./releases)).
2. Kết nối máy tính với AP TOTOLINK N9v1 bằng **dây mạng LAN** và đảm bảo nguồn PoE ổn định.
3. Đăng nhập trang Web của TOTOLINK Stock (`http://192.168.1.165` hoặc IP hiện tại của AP) → vào **Management → Upgrade Firmware**.
4. Chọn file `ConCard_Padavan_N9v1_CSB334A-2700_v1.0.web` và nhấn **Upgrade**.
5. Đợi khoảng **90–120 giây** để thiết bị ghi Flash và khởi động lần đầu.
6. Tìm IP mới của `TOTOLINK-N9V1` trên bảng cấp phát DHCP của Router (hoặc truy cập `http://192.168.1.165` nếu cắm thẳng vào PC đặt IP tĩnh `192.168.1.10/24`) và đăng nhập với `admin` / `admin`.

> **Cập nhật giữa các bản Padavan về sau:** Vào **Administration → Firmware Upgrade** trên giao diện Padavan và tải lên file `.trx` hoặc `.web`.

---

## 6. Cấu Hình Cụm Nhiều AP Chuyển Vùng Mượt `802.11k/r` (`< 30 ms`)

Bản vá **`CONCARD_FT_PSK_LOCAL`** trong `ft.c` cho phép các AP tự dẫn xuất khóa chuyển vùng `PMK-R0` / `PMK-R1` đồng bộ từ mật khẩu Wi-Fi mà **không cần máy chủ Wireless Controller hay cấu hình bảng MAC chéo phức tạp**:

1. Cắm các AP N9v1 vào cùng một mạng LAN / VLAN Layer-2.
2. Trên mỗi AP, vào **Wireless 2.4GHz → General** và đặt **giống hệt nhau**:
   - **SSID:** Tên mạng Wi-Fi chung
   - **Authentication Method:** `WPA2-Personal` (`AES`) + cùng **WPA Pre-Shared Key**
   - **802.11k Neighbor Report (RRM):** `Enable (*)`
   - **802.11r Fast Roaming (FT-PSK):** `Enable (Hybrid WPA2+FT *)`
   - **802.11r Mobility Domain ID:** `CC` (2 ký tự giống nhau trên toàn bộ AP cùng khu vực)
3. Quy hoạch **Channel** xen kẽ không chồng lấn giữa các AP cạnh nhau: **`1` — `6` — `11`** (`Channel Bandwidth: 20 MHz`).
4. Để kiểm tra thực tế thời gian chuyển vùng BSSID và độ trễ gói tin từ laptop Windows:
   ```bash
   node tools/benchmark_roaming_and_capacity.js roam-watch 192.168.1.1 120
   ```

---

## 7. Hướng Dẫn Rollback 1-Click Về Stock Firmware TOTOLINK `V4.0c.2634`

`Padavan-N9v1` đã tích hợp sẵn bộ nhận diện chữ ký `CSB334A-*` trong `user/httpd/upload.c` và cơ chế tự động xóa sạch phân vùng `Config` (`0x30000`) trong `user/rc/rc.c` trước khi nạp lại Firmware hãng:
1. Đăng nhập giao diện Web Padavan → **Administration → Firmware Upgrade**.
2. Chọn file Firmware gốc của hãng (`TOTOLINK_CSB334A_N9_0154A_MT7620A_SPI_8M128M_V4.0c.2634_B20171221_ALL.web`) và nhấn **Upload**.
3. Chờ khoảng **90 giây** để thiết bị tự động làm sạch NVRAM và khởi động lại nguyên bản về giao diện gốc TOTOLINK.

---

## 8. Biên Dịch Lại Từ Mã Nguồn (Ubuntu / WSL2 / GitHub Actions)

### Cấu trúc thư mục dự án
```text
Padavan-N9v1/
├── ci/github-actions-build.yml           # Mẫu workflow CI biên dịch Firmware tự động trên GitHub Actions
├── bsp/
│   ├── board.h                           # Định nghĩa chân GPIO LED/Reset, 128MB RAM, Pure AP Role
│   ├── board.mk                          # Cờ biên dịch -DBOARD_N9V1
│   ├── CSB334A-2700.config               # Cấu hình gói tính năng Padavan & công cụ chẩn đoán
│   └── kernel-3.4.x.config               # Cấu hình nhân Linux 3.4.113 (8MB SPI, Ext PA/LNA, 64 STA, FQ-CoDel)
├── patches/
│   └── concard-n9v1-80211kr-fqcodel-rollback.patch # Bản vá chuẩn unified diff trên cây nguồn rt-n56u
├── releases/
│   ├── ConCard_Padavan_N9v1_CSB334A-2700_v1.0.web  # Ảnh Firmware biên dịch sẵn (nạp trực tiếp từ Web UI)
│   └── SHA256SUMS.txt                    # Mã băm SHA-256 đối chiếu toàn vẹn ảnh Firmware
├── tools/
│   ├── verify_firmware_image.js          # Công cụ kiểm tra header uImage, CRC32 & giới hạn phân vùng mtd4
│   └── benchmark_roaming_and_capacity.js # Công cụ đo chuyển vùng BSSID (802.11k/r) & độ trễ ICMP
├── apply_concard_n9v1_bsp.py             # Trình cài đặt tự động BSP & toàn bộ bản vá mã nguồn
├── build_firmware.sh                     # Script biên dịch trọn gói 1 lệnh trên Ubuntu / WSL2
├── LICENSE                               # Giấy phép nguồn mở GPL-2.0
└── README.md                             # Tài liệu dự án
```

### Các bước tự biên dịch trên Ubuntu 22.04/24.04 hoặc WSL2
```bash
# 1. Cài đặt các gói công cụ biên dịch cần thiết
sudo dpkg --add-architecture i386
sudo apt-get update && sudo apt-get install -y \
  git build-essential gawk pkg-config gettext automake autoconf autopoint \
  libtool-bin bison flex zlib1g-dev libgmp3-dev libmpfr-dev libmpc-dev \
  texinfo python3 kmod cmake gperf unzip curl wget

# 2. Tải cây nguồn Padavan & Toolchain MIPS mipsel-linux-uclibc
sudo git clone --depth=1 https://github.com/hanwckf/rt-n56u.git /opt/rt-n56u
cd /opt/rt-n56u/toolchain-mipsel && sudo ./dl_toolchain.sh

# 3. Áp dụng BSP Padavan-N9v1 và biên dịch ra file .web / .trx
cd /duong/dan/toi/Padavan-N9v1
chmod +x ./build_firmware.sh
sudo ./build_firmware.sh

# 4. Kiểm định chữ ký uImage, CRC32 & dung lượng mtd4
node ./tools/verify_firmware_image.js ./ConCard_Padavan_N9v1_CSB334A-2700_v1.0.web
```

---

## 9. Dự Án Liên Quan & Giấy Phép

- **Phần mềm giám sát tập trung & tối ưu sóng 24h cho dàn AP TOTOLINK N9v1:** [Concard_N9v1 — ConCard AP Monitor](https://github.com/fbaduongth/Concard_N9v1)
- **Giấy phép:** Phát hành theo giấy phép mã nguồn mở **[GNU General Public License v2.0 (GPL-2.0)](./LICENSE)**.
