#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_random.h"
#include "esp_log.h"

static const char *TAG = "ENTROPY_EIGEN";

typedef struct {
    uint32_t trans[2][2];
    uint32_t total_transitions;
} markov_matrix_t;

static void evaluate_entropy_and_spectrum(const uint8_t *buffer, size_t length, float *bias_out, markov_matrix_t *markov, float *lambda2_out) {
    size_t ones_count = 0;
    size_t total_bits = length * 8;
    
    memset(markov, 0, sizeof(markov_matrix_t));
    int prev_bit = -1;

    for (size_t i = 0; i < length; i++) {
        uint8_t byte = buffer[i];
        for (int bit_idx = 0; bit_idx < 8; bit_idx++) {
            int current_bit = (byte >> bit_idx) & 0x01;
            
            if (current_bit) {
                ones_count++;
            }

            if (prev_bit != -1) {
                markov->trans[prev_bit][current_bit]++;
                markov->total_transitions++;
            }
            prev_bit = current_bit;
        }
    }
    *bias_out = (float)ones_count / (float)total_bits;

    // Cálculo de probabilidades de transición
    float p00 = (float)markov->trans[0][0] / (markov->trans[0][0] + markov->trans[0][1]);
    float p11 = (float)markov->trans[1][1] / (markov->trans[1][0] + markov->trans[1][1]);

    // Autovalor secundario lambda_2 (Tasa de mezcla de Markov)
    // lambda_2 = tr(P) - 1 = p00 + p11 - 1
    *lambda2_out = p00 + p11 - 1.0f;
}

void app_main(void) {
    ESP_LOGI(TAG, "=== ESP32-C6 NIST SP 800-90B Spectral Entropy Evaluator ===");
    ESP_LOGI(TAG, "Target: DEKRA Hardware Security Certification Portfolio");

    uint8_t entropy_buffer[256];
    markov_matrix_t markov;

    while (1) {
        esp_fill_random(entropy_buffer, sizeof(entropy_buffer));

        float bias = 0.0f;
        float lambda2 = 0.0f;
        
        evaluate_entropy_and_spectrum(entropy_buffer, sizeof(entropy_buffer), &bias, &markov, &lambda2);

        ESP_LOGI(TAG, "--- Spectral Markov Evaluation ---");
        ESP_LOGI(TAG, "Monobit P(1): %.4f (Ideal: 0.5000)", bias);
        
        if (markov.total_transitions > 0) {
            float p00 = (float)markov.trans[0][0] / (markov.trans[0][0] + markov.trans[0][1]);
            float p01 = (float)markov.trans[0][1] / (markov.trans[0][0] + markov.trans[0][1]);
            float p10 = (float)markov.trans[1][0] / (markov.trans[1][0] + markov.trans[1][1]);
            float p11 = (float)markov.trans[1][1] / (markov.trans[1][0] + markov.trans[1][1]);

            ESP_LOGI(TAG, "Markov Matrix P:");
            ESP_LOGI(TAG, "  [%.4f  %.4f]", p00, p01);
            ESP_LOGI(TAG, "  [%.4f  %.4f]", p10, p11);
            ESP_LOGI(TAG, "Eigenvalues: lambda_1 = 1.0000, lambda_2 = %.4f", lambda2);
            ESP_LOGI(TAG, "Mixing Rate (|lambda_2|): %.4f (Target: near 0.0000)", fabsf(lambda2));
        }

        vTaskDelay(pdMS_TO_TICKS(4000));
    }
}