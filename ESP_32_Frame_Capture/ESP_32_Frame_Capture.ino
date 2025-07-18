#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// Select your camera model (this must match your actual board)
#define CAMERA_MODEL_ESP32S3_EYE
#include "camera_pins.h"

// WiFi credentials for Pi Zero Hotspot
//const char* ssid = "Pulse";
//const char* password = "123456782";
// Flask server endpoint (running on Pi Zero)
const char* serverUrl = "http://192.168.137.123:5000/upload";
//const char* serverUrl = "http://mystick.duckdns.org:5000/upload";
void connectToWiFi() {
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());
}
void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  //different frame resolutions
  // config.frame_size = FRAMESIZE_QQVGA;  // 160x120 (Lowest quality, smallest size)
  // config.frame_size = FRAMESIZE_QCIF;   // 176x144
  // config.frame_size = FRAMESIZE_HQVGA;  // 240x176
  // config.frame_size = FRAMESIZE_QVGA;   // 320x240
  config.frame_size = FRAMESIZE_VGA;    // 640x480 (Default for Pi Zero)
  //config.frame_size = FRAMESIZE_SVGA;   // 800x600
  // config.frame_size = FRAMESIZE_XGA;    // 1024x768
  // config.frame_size = FRAMESIZE_SXGA;   // 1280x1024
  // config.frame_size = FRAMESIZE_UXGA;   // 1600x1200 (Highest quality, largest size)
  config.pixel_format = PIXFORMAT_JPEG;
  config.jpeg_quality = psramFound() ? 15 : 20; // 15 for psram 20 without
  config.fb_count = psramFound() ? 2 : 1; //2 fps for psram 1 fps without
  config.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  config.grab_mode = psramFound() ? CAMERA_GRAB_LATEST : CAMERA_GRAB_WHEN_EMPTY;
  //nitializing camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    while (true); // Stop execution if init fails
  }
  sensor_t* s = esp_camera_sensor_get();
  s->set_vflip(s, 0);
  s->set_brightness(s, 1);
  s->set_saturation(s, 0);
  s->set_framesize(s, FRAMESIZE_VGA);
  s->set_quality(s, config.jpeg_quality);
  Serial.println("Camera initialized.");
}
void uploadImage(camera_fb_t* fb) {
  HTTPClient http;
  http.begin(serverUrl);
  http.addHeader("Content-Type", "image/jpeg");

  int responseCode = http.POST(fb->buf, fb->len);
  if (responseCode > 0) {
    Serial.printf("Image uploaded. Server responded with: %d\n", responseCode);
  } else {
    Serial.printf("Upload failed. Error: %s\n", http.errorToString(responseCode).c_str());
  }

  http.end();
}

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(false); // Turn off if too noisy
  Serial.println("Booting...");

  connectToWiFi();
  initCamera();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi lost. Attempting reconnect...");
    connectToWiFi();
    return;
  }

  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed!");
    delay(2000);
    return;
  }

  uploadImage(fb);
  esp_camera_fb_return(fb);

  delay(1000); // Capture every 1 seconds
}