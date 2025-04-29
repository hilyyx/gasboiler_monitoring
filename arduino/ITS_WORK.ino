#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <Wire.h>
#include <LiquidCrystal_I2C.h>
#include <OneWire.h>
#include <DallasTemperature.h>
#include <EEPROM.h>

// --- Настройки Wi-Fi ---
const char* ssid = "pixel";
const char* password = "30052183";

// --- Настройки сервера ---
const char* server = "http://10.58.167.168:5000"; 
const char* endpoint = "/data";

// --- Пины подключения ---
#define ONE_WIRE_BUS D4  // Пин для DS18B20
#define BUTTON_LEFT D11
#define BUTTON_RIGHT D12

// --- Инициализация объектов ---
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);
LiquidCrystal_I2C lcd(0x27, 16, 2);

WiFiClient client;
HTTPClient http;


unsigned long lastSendTime = 0;
const unsigned long sendInterval = 10000; // каждые 10 секунд отправка

// --- Настройка кнопок ---
bool isMenuPressed = false;
bool isLeftPressed = false;
bool isRightPressed = false;
unsigned long lastButtonPressTime = 0;
const unsigned long screenTimeout = 4000;
unsigned long lastInteractionTime = 0;

#define EEPROM_TIME_ADDR 0
unsigned long fixedTime = 1746160440; 

// --- Функции ---
void connectWiFi() {
  WiFi.begin(ssid, password);
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  lcd.clear();
  lcd.print("WiFi: ");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.SSID());
  delay(2000);
}

void sendDataToServer(float t1, float t2, float t3, float t4, float gasVoltage) {
  if (WiFi.status() == WL_CONNECTED) {
    String url = server + String(endpoint);
    http.begin(client, url);
    http.addHeader("Content-Type", "application/json");

    unsigned long timestamp = millis() / 1000;

    String postData = "{";
    postData += "\"sensor1\": " + String(t1, 2) + ",";
    postData += "\"sensor2\": " + String(t2, 2) + ",";
    postData += "\"sensor3\": " + String(t3, 2) + ",";
    postData += "\"sensor4\": " + String(t4, 2) + ",";
    postData += "\"gas\": " + String(gasVoltage, 2) + ",";
    postData += "\"timestamp\": \"" + String(timestamp) + "\"";
    postData += "}";

    int httpResponseCode = http.POST(postData);
    if (httpResponseCode > 0) {
      Serial.println("Data sent successfully!");
    } else {
      Serial.println("Error sending data!");
    }
    http.end();
  } else {
    Serial.println("WiFi disconnected!");
  }
}

void displayTemperature(float t1, float t2, float t3, float t4) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("T1:");
  lcd.print(t1, 1);
  lcd.print(" T2:");
  lcd.print(t2, 1);

  lcd.setCursor(0, 1);
  lcd.print("T3:");
  lcd.print(t3, 1);
  lcd.print(" T4:");
  lcd.print(t4, 1);
}

void displayGas(float gasVoltage) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Gas:");
  lcd.print(gasVoltage, 2);
  lcd.setCursor(0, 1);
  lcd.print("Time:");
  lcd.print(millis() / 1000);
}

void displayWiFiInfo() {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("WiFi:");
  lcd.setCursor(0, 1);
  lcd.print(WiFi.SSID());
}

void setup() {
  Serial.begin(115200);

  // Инициализация EEPROM
  EEPROM.begin(512);  // Размер памяти EEPROM
  lcd.init();     
  lcd.backlight();

  if (EEPROM.read(EEPROM_TIME_ADDR) == 0xFF) {
    EEPROM.put(EEPROM_TIME_ADDR, fixedTime);
    EEPROM.commit();  // Сохраняем в EEPROM
    Serial.println("Fixed time set.");
  } else {
    // Читаем время из EEPROM
    EEPROM.get(EEPROM_TIME_ADDR, fixedTime);
    Serial.print("Fixed time from EEPROM: ");
    Serial.println(fixedTime);
  }

  connectWiFi();
  sensors.begin();
}

void loop() {
  unsigned long currentMillis = millis();

  // Чтение кнопок
  if (digitalRead(BUTTON_LEFT) == LOW) {
    isLeftPressed = true;
    lastInteractionTime = currentMillis;
  }
  if (digitalRead(BUTTON_RIGHT) == LOW) {
    isRightPressed = true;
    lastInteractionTime = currentMillis;
  }

  // Считываем температуры
  sensors.requestTemperatures();
  float t1 = sensors.getTempCByIndex(0);
  float t2 = sensors.getTempCByIndex(1);
  float t3 = sensors.getTempCByIndex(2);
  float t4 = sensors.getTempCByIndex(3);

  // Считываем газовый датчик
  float gasVoltage = analogRead(A0) * (3.3 / 1023.0);

  if (!isLeftPressed && !isRightPressed) {
    displayTemperature(t1, t2, t3, t4);
  } else if (isLeftPressed) {
    displayGas(gasVoltage);
    isLeftPressed = false;
  } else if (isRightPressed) {
    displayWiFiInfo();
    isRightPressed = false;
  } else if (currentMillis - lastInteractionTime > screenTimeout) {
    displayTemperature(t1, t2, t3, t4); // Автоматический возврат к температуре
  }

  if (currentMillis - lastSendTime > sendInterval) {
    sendDataToServer(t1, t2, t3, t4, gasVoltage);
    lastSendTime = currentMillis;
  }

  delay(100);
}
