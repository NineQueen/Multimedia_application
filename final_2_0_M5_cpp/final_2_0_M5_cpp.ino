#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <M5StickCPlus2.h>
#include <DFRobot_DHT11.h>
#include <time.h>

#define DATA 0 
#define ID 9
#define LED 26
DFRobot_DHT11 dht;

const char *ssid = "TM0512";
const char *password = "05120512";
const char* mqttServer = "ia.ic.polyu.edu.hk";
const int mqttPort = 1883;
const char* mqttUser = "";
const char* mqttPassword = "";
const char* mqttClientId = "GroupA09";
const char* subscribeTopic = "iot/request-A09";
const char* publishTopic = "iot/request-A09";

// NTP服务器配置
const char* ntpServer = "pool.ntp.org";
const long  gmtOffset_sec = 8 * 3600;
const int   daylightOffset_sec = 0;

WiFiClient espClient;
PubSubClient client(espClient);

int count = 0;
unsigned long lastPressTime = 0;
unsigned long lastTimeUpdate = 0;
bool dataReceived = false;
bool dataError = false;
String lastErrorMessage = "";

// 添加内置传感器变量
float internalTemp = 0;
float internalHum = 0;
unsigned long lastSensorRead = 0;
const long sensorInterval = 5000; // 5秒读取一次

struct SensorData {
  String node_id;
  String location;
  float temperature;
  float humidity;
  int light;
  int sound;
} sensorData;

void setup() {
  M5.begin();
  M5.Lcd.setRotation(3);
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setTextSize(1);
  M5.Lcd.setTextColor(WHITE);
  
  sensorData = {"", "", 0.0, 0.0, 0, 0};
  
  connectWiFi();
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  
  client.setServer(mqttServer, mqttPort);
  client.setCallback(callback);
  
  reconnect();
  displayUI();
}

void loop() {
  M5.update();
  
  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  if (millis() - lastTimeUpdate > 60000 || lastTimeUpdate == 0) {
    lastTimeUpdate = millis();
    displayTime();
  }
  
  if (M5.BtnA.wasPressed() && millis() - lastPressTime > 500) {
    lastPressTime = millis();
    sendRequest();
  }
  
  if (dataReceived || dataError) {
    displayUI();
    dataReceived = false;
    dataError = false;
  }
  
  // 添加内置传感器读取和显示
 
  displayInternalSensor();
 

  
}

// 新增函数：读取内置传感器

// 新增函数：显示内置传感器数据
void displayInternalSensor() {
  dht.read(DATA);

  internalHum= dht.humidity;  
  internalTemp = dht.temperature;
  // 在屏幕右侧显示，避免重叠
  int rightX = 100;
  
  // 清除右侧显示区域
  
  
  // 显示内部温度
 if (internalTemp <254)
 {
   M5.Lcd.setCursor(rightX, 30);
   M5.Lcd.setTextColor(WHITE);
   M5.Lcd.print("InTenmp:");
  
   M5.Lcd.setCursor(rightX, 40);
   if(internalTemp > 30) {
     M5.Lcd.setTextColor(RED);
   } else if(internalTemp < 20) {
     M5.Lcd.setTextColor(BLUE);
   } else {
     M5.Lcd.setTextColor(GREEN);
   }
   M5.Lcd.printf("%.1fC", internalTemp);
 }
 
  
  // 显示内部湿度
  if (internalHum < 254)
  {
    M5.Lcd.setCursor(rightX, 50);
    M5.Lcd.setTextColor(WHITE);
    M5.Lcd.print("InHum:");
  
    M5.Lcd.setCursor(rightX, 60);
    if(internalHum > 70) {
     M5.Lcd.setTextColor(CYAN);
    } else if(internalHum < 30) {
     M5.Lcd.setTextColor(ORANGE);
    } else {
     M5.Lcd.setTextColor(GREEN);
    }
    M5.Lcd.printf("%.0f%%", internalHum);
  
    M5.Lcd.setTextColor(WHITE); 
  }
  
}


void displayTime() {
  struct tm timeinfo;
  if(!getLocalTime(&timeinfo)){
    Serial.println("Failed to obtain time");
    return;
  }
  
  char timeString[6];
  strftime(timeString, sizeof(timeString), "%H:%M", &timeinfo);
  
  M5.Lcd.fillRect(120, 0, 40, 10, BLACK);
  M5.Lcd.setCursor(120, 0);
  M5.Lcd.print(timeString);
}

void connectWiFi() {
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.println("Connecting WiFi...");
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    M5.Lcd.print(".");
  }
  M5.Lcd.fillScreen(BLACK);
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.println("WiFi Connected");
  M5.Lcd.print("IP: ");
  M5.Lcd.println(WiFi.localIP());
  
  displayTime();
}

void reconnect() {
  M5.Lcd.setCursor(0, 20);
  M5.Lcd.println("Connecting MQTT...");
  
  while (!client.connected()) {
    if (client.connect(mqttClientId, mqttUser, mqttPassword)) {
      M5.Lcd.fillRect(0, 20, 160, 10, BLACK);
      M5.Lcd.setCursor(0, 20);
      M5.Lcd.println("MQTT Connected");
      client.subscribe(subscribeTopic);
    } else {
      M5.Lcd.print("Failed, rc=");
      M5.Lcd.print(client.state());
      M5.Lcd.println(" Retry in 5s");
      delay(5000);
    }
  }
}

void sendRequest() {
  DynamicJsonDocument doc(128);
  doc["count"] = count;
  String request;
  serializeJson(doc, request);
  
  digitalWrite(LED, HIGH);
  delay(100);
  digitalWrite(LED, LOW);
  
  if (client.publish(publishTopic, request.c_str())) {
    M5.Lcd.fillRect(0, 80, 160, 20, BLACK);
    M5.Lcd.setCursor(0, 80);
    M5.Lcd.print("Sent: ");
    M5.Lcd.println(request);
    
    count++;
    M5.Lcd.fillRect(0, 40, 50, 10, BLACK);
    M5.Lcd.setCursor(0, 40);
    M5.Lcd.print("Count: ");
    M5.Lcd.println(count);
  } else {
    lastErrorMessage = "Send failed";
    dataError = true;
  }
}

void callback(char* topic, byte* payload, unsigned int length) {
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED, HIGH);
    delay(50);
    digitalWrite(LED, LOW);
    delay(50);
  }
  
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  
  if (!parseSensorData(message)) {
    lastErrorMessage = "Invalid data format";
    dataError = true;
  } else {
    dataReceived = true;
  }
}

bool parseSensorData(String json) {
  DynamicJsonDocument doc(256);
  DeserializationError error = deserializeJson(doc, json);
  
  if (error) {
    lastErrorMessage = "JSON parse error";
    return false;
  }
  
  if (!doc.containsKey("node_id") || !doc.containsKey("loc") || 
      !doc.containsKey("temp") || !doc.containsKey("hum") ||
      !doc.containsKey("light") || !doc.containsKey("snd")) {
    lastErrorMessage = "Missing fields";
    return false;
  }
  
  try {
    sensorData.node_id = doc["node_id"].as<String>();
    sensorData.location = doc["loc"].as<String>();
    
    if (doc["temp"].is<String>()) {
      sensorData.temperature = doc["temp"].as<String>().toFloat();
    } else {
      sensorData.temperature = doc["temp"].as<float>();
    }
    
    if (doc["hum"].is<String>()) {
      sensorData.humidity = doc["hum"].as<String>().toFloat();
    } else {
      sensorData.humidity = doc["hum"].as<float>();
    }
    
    if (doc["light"].is<String>()) {
      sensorData.light = doc["light"].as<String>().toInt();
    } else {
      sensorData.light = doc["light"].as<int>();
    }
    
    if (doc["snd"].is<String>()) {
      sensorData.sound = doc["snd"].as<String>().toInt();
    } else {
      sensorData.sound = doc["snd"].as<int>();
    }
    
    return true;
  } catch (...) {
    lastErrorMessage = "Data processing error";
    return false;
  }
}

void displayUI() {
  M5.Lcd.fillScreen(BLACK);
  
  // 显示时间
  displayTime();
  
  // 显示电量（添加能量柱）
  int batteryLevel = M5.Power.getBatteryLevel();
  int batteryWidth = map(batteryLevel, 0, 100, 0, 20);
  
  // 绘制电池外框
  M5.Lcd.drawRect(M5.Lcd.width() - 25, M5.Lcd.height() - 12, 22, 10, WHITE);
  // 绘制电池正极
  M5.Lcd.fillRect(M5.Lcd.width() - 3, M5.Lcd.height() - 10, 2, 5, WHITE);
  
  // 根据电量水平设置能量柱颜色
  uint16_t batteryColor;
  if(batteryLevel > 60) {
    batteryColor = GREEN;
  } else if(batteryLevel > 30) {
    batteryColor = YELLOW;
  } else {
    batteryColor = RED;
  }
  
  // 绘制能量柱
  M5.Lcd.fillRect(M5.Lcd.width() - 24, M5.Lcd.height() - 11, batteryWidth, 8, batteryColor);
  
  // 显示电量百分比
  M5.Lcd.setTextColor(WHITE);
  M5.Lcd.setCursor(M5.Lcd.width() - 45, M5.Lcd.height() - 10);
  M5.Lcd.printf("%d%%", batteryLevel);
  
  // 显示连接状态
  M5.Lcd.setCursor(0, 0);
  M5.Lcd.print("WiFi: ");
  M5.Lcd.println(WiFi.SSID());
  M5.Lcd.setCursor(0, 10);
  M5.Lcd.print("MQTT: ");
  M5.Lcd.println(client.connected() ? "OK" : "Disconnected");
  
  // 显示计数器
  M5.Lcd.setCursor(0, 20);
  M5.Lcd.print("Count: ");
  M5.Lcd.println(count);
  
  if (dataError) {
    M5.Lcd.setCursor(0, 40);
    M5.Lcd.setTextColor(RED);
    M5.Lcd.println("Error:");
    M5.Lcd.println(lastErrorMessage);
    M5.Lcd.setTextColor(WHITE);
    return;
  }
  
  // 显示传感器数据
  int yPos = 40;
  M5.Lcd.setCursor(0, yPos);
  M5.Lcd.print("ID: ");
  M5.Lcd.println(sensorData.node_id);
  yPos += 10;
  
  M5.Lcd.setCursor(0, yPos);
  M5.Lcd.print("Loc: ");
  M5.Lcd.println(sensorData.location);
  yPos += 10;
  
  // 温度显示 - 添加图标
  M5.Lcd.setCursor(0, yPos);
  if(sensorData.temperature > 27.0) {
    M5.Lcd.setTextColor(RED);
  } else if(sensorData.temperature < 23.0) {
    M5.Lcd.setTextColor(BLUE);
  } else {
    M5.Lcd.setTextColor(WHITE);
  }
  M5.Lcd.print("Temp: ");
  M5.Lcd.print(sensorData.temperature, 1);
  M5.Lcd.print("C");
  
  // 添加温度图标显示
  int tempTextWidth = 60; // 预估温度文本宽度
  int iconX = tempTextWidth; // 图标X位置
  int iconY = yPos;        // 图标Y位置
  
  // 清除图标区域
  M5.Lcd.fillRect(iconX, iconY, 20, 10, BLACK);
  
  if(sensorData.temperature < 23.0) {
    M5.Lcd.setTextColor(BLUE);
    M5.Lcd.setCursor(iconX, iconY);
    M5.Lcd.print(" Cold");
  } else if(sensorData.temperature > 27.0) {
    M5.Lcd.setTextColor(RED);
    M5.Lcd.setCursor(iconX, iconY);
    M5.Lcd.print(" Hot");
  }
  M5.Lcd.setTextColor(WHITE); // 恢复默认颜色
  
  yPos += 10;
  
  M5.Lcd.setCursor(0, yPos);
  M5.Lcd.print("Hum: ");
  M5.Lcd.print(sensorData.humidity, 1);
  M5.Lcd.println("%");
  yPos += 10;
  
  M5.Lcd.setCursor(0, yPos);
  M5.Lcd.print("Light: ");
  M5.Lcd.print(sensorData.light);
  M5.Lcd.println("lx");
  yPos += 10;
  
  M5.Lcd.setCursor(0, yPos);
  M5.Lcd.print("Sound: ");
  M5.Lcd.print(sensorData.sound);
  M5.Lcd.println("dB");
  
  // 操作提示
  M5.Lcd.setCursor(0, M5.Lcd.height() - 10);
  M5.Lcd.println("Press BTN to request");
}
