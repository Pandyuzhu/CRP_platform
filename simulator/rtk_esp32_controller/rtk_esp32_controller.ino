#include <WiFi.h>
#include <WiFiUdp.h>
#include <math.h>

// 网络配置
const char *ssid = "哇咔咔咔";
const char *password = "17703405740";

// UDP配置
WiFiUDP udp;
const char *remoteIP = "192.168.32.169";  // 目标IP（计算机）
const int remotePort = 60001;              // 目标端口

// 模拟RTK设备
String deviceID = "rtk1";
float radius = 0.01;  // 圆周运动半径
float speed = 0.1;    // 运动速度
float angle = 0.0;    // 当前角度
float e = 0.0, n = 0.0, u = 0.0;  // 设备的ENU坐标

// 定义WiFi连接函数
void connectToWiFi() {
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");
}

void setup() {
  Serial.begin(115200);
  connectToWiFi();
  udp.begin(60000);  // 本地端口
}

void loop() {
  static unsigned long lastTime = 0;
  unsigned long currentTime = millis();
  
  // 模拟圆周运动，每秒更新一次
  if (currentTime - lastTime >= 100) {
    // 计算圆周运动的位置
    angle += (speed / radius) * 0.1;  // 角速度 = 线速度 / 半径
    
    e = radius * cos(angle);  // 更新 E 坐标
    n = radius * sin(angle);  // 更新 N 坐标
    u = 0.0;  // 高度保持不变
    
    // 打包数据包并发送
    sendRTKData(currentTime);
    
    lastTime = currentTime;
  }
}

void sendRTKData(unsigned long timestamp) {
  byte packet[24];  // 数据包大小（8字节设备ID + 16字节数据）
  
  // 设备ID（最多8字节）
  String device = deviceID;
  for (int i = 0; i < 8; i++) {
    if (i < device.length()) {
      packet[i] = device[i];
    } else {
      packet[i] = 0;  // 补充0
    }
  }
  
  // 时间戳（4字节）
  packet[8] = (timestamp >> 24) & 0xFF;
  packet[9] = (timestamp >> 16) & 0xFF;
  packet[10] = (timestamp >> 8) & 0xFF;
  packet[11] = timestamp & 0xFF;
  
  // ENU坐标（每个4字节）
  memcpy(packet + 12, &e, sizeof(float));
  memcpy(packet + 16, &n, sizeof(float));
  memcpy(packet + 20, &u, sizeof(float));
  
  // 发送UDP数据包
  udp.beginPacket(remoteIP, remotePort);
  udp.write(packet, sizeof(packet));
  udp.endPacket();
  
  Serial.printf("Sending data: E=%.3f, N=%.3f, U=%.3f\n", e, n, u);
}
