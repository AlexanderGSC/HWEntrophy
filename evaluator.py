# This script captures the lines of the CSV file sent by 
# the microcontroller via the serial port and generates a statistical 
# analysis of the data.

import sys
import time
import csv
import statistics
import serial
import matplotlib.pyplot as plt

PORT = "/dev/ttyACM0"
BAUD = 115200
CSV_FILE = "entropy_metrics.csv"
REPORT_FILE = "entropy_report.txt"

# Lists
timestamps = []
monobit_p1 = []
mixing_rates = []
p00_list = []
p01_list = []
p10_list = []
p11_list = []

print(f"[*] Connecting serial port {PORT} at {BAUD} baud...")

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)
    ser.reset_input_buffer()
except Exception as e:
    print(f"[!] Error opening serial port: {e}")
    sys.exit(1)

print("[*] Capturing entropy data from the ESP32-C6. Press Ctrl+C to finish, plot, and generate a report.")

try:
    with open(CSV_FILE, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_ms", "monobit_p1", "p00", "p01", "p10", "p11", "lambda_2", "mixing_rate"])
        
        while True:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line:
                continue
            
            if line.startswith("CSV_DATA:"):
                clean_line = line.replace("CSV_DATA:", "")
                parts = clean_line.split(",")
                
                if len(parts) == 8:
                    writer.writerow(parts)
                    f.flush()
                    
                    try:
                        ts = float(parts[0]) / 1000.0
                        p1 = float(parts[1])
                        p_00 = float(parts[2])
                        p_01 = float(parts[3])
                        p_10 = float(parts[4])
                        p_11 = float(parts[5])
                        m_rate = float(parts[7])
                        
                        # Save values
                        timestamps.append(ts)
                        monobit_p1.append(p1)
                        mixing_rates.append(m_rate)
                        p00_list.append(p_00)
                        p01_list.append(p_01)
                        p10_list.append(p_10)
                        p11_list.append(p_11)
                        
                        print(f"[Capture] Time: {ts:.2f}s | P(1): {p1:.4f} | p(0→0): {p_00:.3f} | p(0→1): {p_01:.3f} | p(1→1): {p_11:.3f} | p(1→0): {p_10:.3f} | λ₂: {m_rate:.4f}")
                    except ValueError:
                        continue

except KeyboardInterrupt:
    print("\n[!] Capture stopped by the user.")
finally:
    ser.close()
    print(f"\n[+] Data saved in '{CSV_FILE}'. Calculating statistics and generating report...")

    if timestamps:
        # STATISTICS
        def get_stats(data):
            if not data:
                return 0.0, 0.0
            mean_val = statistics.mean(data)
            stdev_val = statistics.stdev(data) if len(data) > 1 else 0.0
            return mean_val, stdev_val

        p1_mean, p1_std = get_stats(monobit_p1)
        mix_mean, mix_std = get_stats(mixing_rates)
        p00_mean, p00_std = get_stats(p00_list)
        p01_mean, p01_std = get_stats(p01_list)
        p10_mean, p10_std = get_stats(p10_list)
        p11_mean, p11_std = get_stats(p11_list)

        # Construir el texto del reporte
        report_lines = [
            "=" * 65,
            "ENTROPY STATISTICAL EVALUATION REPORT",
            "=" * 65,
            f" Date and Time of the Report: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f" Device:              ESP32-C6 (TRNG Evaluator)",
            f" Number of Sampless:        {len(timestamps)}",
            f" Duration of the capture:   {timestamps[-1] - timestamps[0]:.1f} seconds",
            "-" * 65,
            f" Monobit P(1)       -> μ: { p1_mean:.4f}  |  σ: { p1_std:.5f}  --Ideal: ~N(0.5,0.0)",
            f" Mix Rate           -> μ: {mix_mean:.4f}  |  σ: {mix_std:.5f}  --Ideal: ~N(0.0,0.0)",
            f" Transition 0→0     -> μ: {p00_mean:.4f}  |  σ: {p00_std:.5f}  --Ideal: ~N(0.5,0.0)",
            f" Transition 0→1     -> μ: {p01_mean:.4f}  |  σ: {p01_std:.5f}  --Ideal: ~N(0.5,0.0)",
            f" Transition 1→0     -> μ: {p10_mean:.4f}  |  σ: {p10_std:.5f}  --Ideal: ~N(0.5,0.0)",
            f" Transition 1→1     -> μ: {p11_mean:.4f}  |  σ: {p11_std:.5f}  --Ideal: ~N(0.5,0.0)",
            "=" * 65
        ]

        report_text = "\n".join(report_lines)

        # Print
        print("\n" + report_text + "\n")

        # Save report
        try:
            with open(REPORT_FILE, "w", encoding="utf-8") as rep:
                rep.write(report_text + "\n")
            print(f"[+] Report successfully saved as '{REPORT_FILE}'.")
        except Exception as e:
            print(f"[!] Error saving the report file: {e}")

        # --- BLOQUE DE GRÁFICAS ---
        print("[+] Generating Plots...")
        plt.figure(figsize=(12, 10))
        
        # Subplot 1: Monobit P(1)
        plt.subplot(3, 1, 1)
        plt.plot(timestamps, monobit_p1, label="Monobit P(1)", color="blue", linewidth=1.5)
        plt.axhline(0.5, color="red", linestyle="--", label="Ideal P(1) = 0.5")
        plt.ylabel("Bit Ratio (1)")
        plt.title("ESP32-C6 TRNG Analysis")
        plt.legend(loc="upper right")
        plt.grid(True)

        # Subplot 2: Mix Rate
        plt.subplot(3, 1, 2)
        plt.plot(timestamps, mixing_rates, label="Mixing Rate |λ₂|", color="green", linewidth=1.5)
        plt.axhline(0.0, color="red", linestyle="--", label="Ideal Independence (0)")
        plt.ylabel("Mix Rate (|λ₂|)")
        plt.legend(loc="upper right")
        plt.grid(True)

        # Subplot 3: Markov Transitions
        plt.subplot(3, 1, 3)
        plt.plot(timestamps, p00_list, label="p00 (0→0)", color="orange", alpha=0.8)
        plt.plot(timestamps, p01_list, label="p01 (0→1)", color="purple", alpha=0.8)
        plt.plot(timestamps, p10_list, label="p10 (1→0)", color="brown", alpha=0.8)
        plt.plot(timestamps, p11_list, label="p11 (1→1)", color="cyan", alpha=0.8)
        plt.axhline(0.5, color="red", linestyle="--", label="Ideal Transition = 0.5")
        plt.xlabel("Time (secs)")
        plt.ylabel("Transition Probabilities")
        plt.legend(loc="upper right", ncol=5)
        plt.grid(True)

        plt.tight_layout()
        plt.savefig("entropy_analysis_plot.png")
        print("[+] Plot successfully saved as 'entropy_analysis_plot.png'.")
        plt.show()
    else:
        print("[!] No valid data was collected to generate the graph and report.")