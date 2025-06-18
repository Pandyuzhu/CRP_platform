#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>

const char* ssid = "你的WiFi名称";
const char* password = "你的WiFi密码";

WiFiUDP udp;
const unsigned int localPort = 12345;  // 与Python端保持一致

// 控制参数
String targetIP = "10.192.32.169";
int targetPort = 60001;

float ref_lat = 32.0806422;
float ref_lon = 119.301785;
float ref_alt = 66.0;

bool simulation_running = false;
unsigned long lastSendTime = 0;
const unsigned long sendInterval = 100; // 10Hz

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);
  Serial.println("连接WiFi中...");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\n已连接WiFi，IP地址为: ");
  Serial.println(WiFi.localIP());

  udp.begin(localPort);
  Serial.println("UDP监听已启动");
}

void loop() {
  receiveCommand();

  if (simulation_running && millis() - lastSendTime >= sendInterval) {
    sendSimulatedRTKPacket();
    lastSendTime = millis();
  }
}

void receiveCommand() {
  int packetSize = udp.parsePacket();
  if (packetSize > 0) {
    char incomingPacket[512];
    int len = udp.read(incomingPacket, 512);
    if (len > 0) {
      incomingPacket[len] = '\0';
    }

    Serial.print("收到UDP命令: ");
    Serial.println(incomingPacket);

    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, incomingPacket);
    if (error) {
      Serial.print("JSON解析失败: ");
      Serial.println(error.c_str());
      return;
    }

    String cmd = doc["command"] | "";
    if (cmd == "start") {
      targetIP = doc["target_ip"] | targetIP;
      targetPort = doc["target_port"] | targetPort;
      ref_lat = doc["ref_lat"] | ref_lat;
      ref_lon = doc["ref_lon"] | ref_lon;
      ref_alt = doc["ref_alt"] | ref_alt;
      simulation_running = true;
      Serial.println("开始模拟RTK发送...");
    } else if (cmd == "stop") {
      simulation_running = false;
      Serial.println("已停止RTK模拟");
    }
  }
}

void sendSimulatedRTKPacket() {
  // 简单模拟 ENU 位移，可根据需要替换为真实模型
  static float angle = 0.0;
  float radius = 5.0;
  float e = radius * cos
