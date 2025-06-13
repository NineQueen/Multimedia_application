#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <LedControl.h>

// 引脚定义（根据实际连接修改）
#define DIN_PIN D7    // MOSI (GPIO13)
#define CLK_PIN D5    // SCK (GPIO14)
#define CS_PIN D4     // CS (GPIO2)
#define RED_LED_PIN D0 // 传统RGB红灯引脚
#define GREEN_LED_PIN D8 // 传统RGB绿灯引脚
#define BLUE_LED_PIN D3 // 传统RGB蓝灯引脚
#define BUTTON_PIN D2  // 按钮S1连接到D2引脚

LedControl lc = LedControl(DIN_PIN, CLK_PIN, CS_PIN, 1); // 1个MAX7219设备

// WiFi and MQTT configuration
const char *ssid = "TM0512";
const char *password = "05120512";
const char *mqtt_server = "ia.ic.polyu.edu.hk";
const int mqttPort = 1883;
const char *mqttTopic = "iot/sensor-A";
const char *mqttButtonTopic = "iot/sensor-A009"; 

WiFiClient espClient;
PubSubClient client(espClient);

// Temperature threshold setting
const float HIGH_TEMP_THRESHOLD = 30.0;
const float LOW_TEMP_THRESHOLD = 10.0;

// Rounded flame pattern (smooth edges and rich layers)
const byte flamePattern[8] = {
  B00001000,
  B00011100,
  B00111110,
  B01111111,
  B01111111,
  B00111110,
  B00011100,
  B00001000
};

// Rounded snowflake pattern (soft edges, strong three-dimensional effect)
const byte snowflakePattern[8] = {
  B00011000,
  B00111100,
  B01100110,
  B11011011,
  B01100110,
  B00111100,
  B00011000,
  B00000000
};

int lastButtonState = HIGH;
int currentButtonState;
unsigned long lastDebounceTime = 0;
unsigned long debounceDelay = 50; 
//set color
void setColor(int r, int g, int b) {
  analogWrite(RED_LED_PIN, r);
  analogWrite(GREEN_LED_PIN, g);
  analogWrite(BLUE_LED_PIN, b);
  Serial.printf("RGB settings: red=%d, green=%d, blue=%d\n", 255-r, 255-g, 255-b);
}

// template pattern
void displayFlame() {
  for (int row = 0; row < 8; row++) {
    lc.setRow(0, row, flamePattern[row]);
  }
}

// snowflake pattern
void displaySnowflake() {
  for (int row = 0; row < 8; row++) {
    lc.setRow(0, row, snowflakePattern[row]);
  }
}
void sendButtonMessage() {
  if (client.connected()) {
    client.publish(mqttButtonTopic, "start");
    Serial.println("Send message: start");
    // Visual feedback of button presses
    setColor(255, 255, 0); // yellow flashing
    delay(200);
    setColor(255, 0, 255); // Return to green
  } else {
    Serial.println("MQTT is not connected and cannot send messages");
  }
}

// 8x8 matrix control
void setMatrixDisplay(int pattern) {
  lc.clearDisplay(0); // clear display
  
  switch (pattern) {
    case 1: // Red Mode - Flame
      setColor(0, 255, 255);    // Traditional RGB red lights are all on
      displayFlame();
      break;
    case 2: // Blue Pattern - Snowflakes
      setColor(255, 255, 0);    // Traditional RGB blue light is fully lit
      displaySnowflake();
      break;
    default: // Green mode - off
      setColor(255, 0, 255);    // Traditional RGB green lights are all on
      lc.clearDisplay(0);       // Matrix turns off
      break;
  }
}


void callback(char* topic, byte* payload, unsigned int length) {
  String msg = String((char*)payload).substring(0, length);
  Serial.printf("Received message: %s\n", msg.c_str());

  // Parse the temperature value (for the new format: "temp": "26.0")
  float temperature = parseTemperature(msg);

  if (!isnan(temperature)) {
    Serial.printf("Parse to temperature: %.1f°C\n", temperature);
    setMatrixDisplay(temperature > HIGH_TEMP_THRESHOLD ? 1 : 
                    (temperature < LOW_TEMP_THRESHOLD ? 2 : 0));
  } else {
    Serial.println("Temperature analysis failed");
    setColor(255, 255, 0); 
    lc.clearDisplay(0);     
  }
}

// Temperature analysis function (adapt to "temp": "26.0" format)
float parseTemperature(String jsonStr) {
  // Find the location of "temp": "
  int startIndex = jsonStr.indexOf("\"temp\": \"");
  if (startIndex == -1) return NAN; // Temperature field not found

  // Locate the end of the temperature value (next double quote)
  int endIndex = jsonStr.indexOf("\"", startIndex + 9); // "temp": " 占8个字符
  if (endIndex == -1 || endIndex <= startIndex) return NAN;

 // Extract the temperature string and convert it to a floating point number
  String tempStr = jsonStr.substring(startIndex + 9, endIndex);
  return tempStr.toFloat();
}


boolean reconnect() {
  if(client.connect("ESP8266-TempMonitor")) {
    client.subscribe(mqttTopic);
    setMatrixDisplay(0);        // 矩阵熄灭（绿色模式）
    Serial.println("MQTT connection successful");
    return true;
  }
  
  setColor(0, 255, 255);      // 连接失败：红灯
  Serial.printf("MQTT连接失败，错误码: %d\n", client.state());
  return false;
}

void setup() {
  Serial.begin(115200);
  
  // 初始化LED引脚
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(BLUE_LED_PIN, OUTPUT);
  
  // 初始化MAX7219矩阵
  lc.shutdown(0, false);      // 退出关机模式
  lc.setIntensity(0, 8);      // 设置亮度 (0-15)
  lc.clearDisplay(0);         // 清除显示
    // 初始化按钮引脚（上拉输入）
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  // 连接WiFi
  WiFi.begin(ssid, password);
  while(WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi连接成功");
  
  // 连接MQTT服务器
  client.setServer(mqtt_server, mqttPort);
  client.setCallback(callback);
}

void loop() {
  if(!client.connected()) {
    reconnect();
  }
  
  client.loop();

  // 读取按钮状态并进行消抖处理
  int reading = digitalRead(BUTTON_PIN);
  
  // 如果状态改变，记录时间
  if (reading != lastButtonState) {
    lastDebounceTime = millis();
  }
  
  // 经过消抖延迟后确认状态
  if ((millis() - lastDebounceTime) > debounceDelay) {
    if (reading != currentButtonState) {
      currentButtonState = reading;
      
      // 检测到按钮按下（从HIGH变为LOW）
      if (currentButtonState == LOW) {
        sendButtonMessage();
      }
    }
  }
  
  lastButtonState = reading;
  delay(100);
}
