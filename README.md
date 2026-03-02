# 📡 Automated IoT Provisioning & Monitoring Station

This project is a **Linux-based automation system** built on a Raspberry Pi to flash and monitor up to **4 ESP32 devices** efficiently.  
It eliminates manual flashing by automatically detecting connected ESP32 boards using their **MAC addresses** and flashing the correct firmware while displaying progress on a **simple live web dashboard**.

---

## 🔄 Flashing Workflow

The flashing process operates in a **sequential manner**, meaning ESP32 devices are flashed **one by one**, not in parallel.

- When an ESP32 is connected, the system checks whether it has already been flashed.
- If the device is **new** or has been **unplugged and plugged in again**, firmware flashing starts automatically.
- If the ESP32 remains connected after a successful flash, it **will not be flashed again**.
- Each ESP32 is flashed **only once per connection cycle**.

---

## 🛠️ Fault Handling & Retry Logic

If firmware flashing **gets stuck or fails** for a specific ESP32:

- That device is **temporarily skipped** and queued for the **next iteration**.
- The system continues flashing other connected ESP32 devices without interruption.
- After completing one full cycle, the skipped ESP32 is retried.

This mechanism ensures **reliability** and prevents a single faulty device from blocking the entire flashing process.

---

## 🌐 Software Architecture

The system is developed using **Python 3** and leverages:

- **Flask** and **Flask-SocketIO** for the live web dashboard
- **esptool.py** for firmware flashing
- **Linux udev utilities** to maintain stable USB device mapping across reboots

The web dashboard provides:
- Real-time logs  
- Flashing progress  
- Success and failure status for each ESP32  

---

## 📦 Firmware Handling

Firmware flashing uses a **single merged binary file** instead of multiple separate binaries.

- The merged binary includes the **bootloader**, **partition table**, and **application code**
- This approach improves flashing reliability and consistency
- Firmware files are stored in the `/firmware` directory
- Each ESP32 is assigned firmware based on its **MAC address**

---

## 🔌 Hardware & Power Setup

For stable operation:

- All ESP32 devices are connected to the Raspberry Pi through a **powered USB hub**
- Power and data are supplied entirely over USB, which inherently provides a common ground between the Raspberry Pi and all connected ESP32 boards.
- This setup ensures reliable serial communication and prevents flashing failures caused by power instability or noise.

---

## 📁 Repository Scope

This repository focuses only on:
- Flashing automation logic  
- Device handling workflow  
- Monitoring dashboard  

⚠️ The **Arduino source code** used to generate firmware binaries is **proprietary** and **not included**.

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 👤 Author

**Jerit Jose**  
Embedded Systems & IoT Developer
