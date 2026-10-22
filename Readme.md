# ESP32-C6 Hardware Entropy & Markov Evaluator

Firmware de validación Criptográfica para evaluación de seguridad de hardware y criptografía aplicada.

### Descripción General

Este proyecto implementa un evaluador de entropía en tiempo real ejecutándose sobre un microcontrolador ESP32-C6 (RISC-V). Su propósito es adquirir números aleatorios reales mediante el subsistema físico TRNG (True Random Number Generator) del chip y verificar analíticamente su calidad estadística e independencia temporal de acuerdo con las directrices de los estándares NIST SP 800-90B y FIPS 140-3, requisitos indispensables en laboratorios de certificación de dispositivos seguros como DEKRA.

### Arquitectura y Componentes del Sistema

Adquisición de Entropía por Hardware:Interacción directa con el núcleo TRNG integrado en el ESP32-C6 mediante la API de ESP-IDF (esp_fill_random), el cual alimenta su semilla a partir del ruido térmico y analógico de los circuitos de radiofrecuencia (Wi-Fi 6 / IEEE 802.15.4).Prueba Preliminar Monobit ($P(1)$):Evalúa la proporción de bits en alto (1) frente al total de la muestra. El objetivo estricto de diseño es mantener la probabilidad $P(1) \approx 0.5000$, validando la ausencia de sesgo en amplitud.Modelo de Matriz de Transición de Markov (1er Orden):Construcción en tiempo real de una matriz estocástica $2 \times 2$ para medir la probabilidad condicional de transición entre bits consecutivos ($P(0\vert{}0)$, $P(1\vert{}0)$, $P(0\vert{}1)$, $P(1\vert{}1)$), detectando cualquier dependencia de memoria temporal.Análisis Espectral (Autovalores / Eigenvalues):Cálculo analítico del autovalor secundario ($\lambda_2$) de la matriz de Markov a partir de su traza ($\lambda_2 = \text{tr}(P) - 1$).Tasa de Mezcla (Mixing Rate): Cuantificación de $\vert{}\lambda_2\vert{} \approx 0.0000$, certificando la independencia asintótica exigida por los laboratorios de ensayo.

## Fragmento del Código (C / ESP-IDF)

El núcleo del motor matemático implementado en el firmware (main/main.c):C// Cálculo analítico del autovalor secundario lambda_2 (Tasa de mezcla de Markov)

```c
// Demuestra la independencia asintótica exigida por NIST SP 800-90B
float p00 = (float)markov->trans[0][0] / (markov->trans[0][0] + markov->trans[0][1]);
float p11 = (float)markov->trans[1][1] / (markov->trans[1][0] + markov->trans[1][1]);

// lambda_2 = tr(P) - 1 = p00 + p11 - 1
float lambda2 = p00 + p11 - 1.0f;
float mixing_rate = fabsf(lambda2); // Objetivo: tender a 0.0000
```

## Resultados Empíricos (Monitor Serie en Placa Real)

Captura de la ejecución sobre un ESP32-C6 (QFN40) real mapeado mediante WSL y usbipd:PlaintextI (318) 

```text
ENTROPY_EIGEN: --- Spectral Markov Evaluation ---
I (318) ENTROPY_EIGEN: Monobit P(1): 0.4971 (Ideal: 0.5000)
I (328) ENTROPY_EIGEN: Markov Matrix P:
I (328) ENTROPY_EIGEN:   [0.4981  0.5019]
I (328) ENTROPY_EIGEN:   [0.5084  0.4916]
I (338) ENTROPY_EIGEN: Eigenvalues: lambda_1 = 1.0000, lambda_2 = -0.0103
I (338) ENTROPY_EIGEN: Mixing Rate (|lambda_2|): 0.0103 (Target: near 0.0000)
```
### Entorno de Desarrollo y Despliegue Hardware: ESP32-C6

(RISC-V 32-bit RV32IMAC, conversor USB-UART WCH CH343).Software SDK: ESP-IDF v5.1.2 (Versión LTS estable para entornos industriales y de certificación).Entorno de Contenedores: Docker (espressif/idf:v5.1.2) garantizando compilaciones incrementales limpias y aislamiento de dependencias Python/Toolchain.Sistema Host: Windows 11 con WSL2 (Ubuntu) y mapeo directo de puertos serie por USB/IP (usbipd-win en /dev/ttyACM0).