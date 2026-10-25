#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_system.h"
#include "esp_random.h"
#include "esp_log.h"

#define RGB_BUILTIN 8

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

    float p00 = (float)markov->trans[0][0] / (markov->trans[0][0] + markov->trans[0][1]);
    float p11 = (float)markov->trans[1][1] / (markov->trans[1][0] + markov->trans[1][1]);

    *lambda2_out = p00 + p11 - 1.0f;
}


void app_main(void) {

    // Initial Delay
    //vTaskDelay(pdMS_TO_TICKS(1500));

    // Print Header
    printf("CSV_HEADER:timestamp_ms,monobit_p1,p00,p01,p10,p11,lambda_2,mixing_rate\n");

    uint8_t entropy_buffer[256];
    markov_matrix_t markov;

    uint32_t sample_counter = 0;

    while (1) {

        esp_fill_random(entropy_buffer, sizeof(entropy_buffer));

        float bias = 0.0f;
        float lambda2 = 0.0f;
        
        evaluate_entropy_and_spectrum(entropy_buffer, sizeof(entropy_buffer), &bias, &markov, &lambda2);

        if (markov.total_transitions > 0) {
            float p00 = (float)markov.trans[0][0] / (markov.trans[0][0] + markov.trans[0][1]);
            float p01 = (float)markov.trans[0][1] / (markov.trans[0][0] + markov.trans[0][1]);
            float p10 = (float)markov.trans[1][0] / (markov.trans[1][0] + markov.trans[1][1]);
            float p11 = (float)markov.trans[1][1] / (markov.trans[1][0] + markov.trans[1][1]);

            // CSV Format
            printf("CSV_DATA:%lu,%6.4f,%6.4f,%6.4f,%6.4f,%6.4f,%6.4f,%6.4f\n",
                   (unsigned long)(xTaskGetTickCount() * portTICK_PERIOD_MS),
                   bias, p00, p01, p10, p11, lambda2, fabsf(lambda2));
        }

        sample_counter++;
        vTaskDelay(pdMS_TO_TICKS(500)); // 0.5 Sec sample delay   
    }
}