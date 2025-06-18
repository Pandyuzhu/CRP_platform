#include <WiFi.h>
#include <WiFiUdp.h>

// WiFi设置
const char* ssid = "哇咔咔咔";  // 替换为你的WiFi名称
const char* password = "17703405740";  // 替换为你的WiFi密码

// UDP设置
WiFiUDP udp;
unsigned int localPort = 60001;  // 与Python脚本中的目标端口一致
char incomingPacket[255];  // 存储接收到的UDP数据包
char replyPacket[] = "Message received";  // 响应内容

// 设备ID
const String deviceId = "rtk1";  // 设置设备ID

void setup() {
  // 启动串口通信
  Serial.begin(115200);
  
  // 连接WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("Connected to WiFi");

  // 启动UDP
  udp.begin(localPort);
  Serial.print("UDP listening on port ");
  Serial.println(localPort);
}

void loop() {
  // 检查是否有收到UDP数据包
  int packetSize = udp.parsePacket();
  if (packetSize) {
    // 接收数据包
    int len = udp.read(incomingPacket, 255);
    if (len > 0) {
      incomingPacket[len] = 0;  // 确保字符串终止
    }
    Serial.print("Received packet: ");
    Serial.println(incomingPacket);

    // 模拟接收到的数据包（RTK数据包格式：设备ID + 时间戳 + ENU坐标）
    // 这里你可以解析数据包并根据实际需求做进一步的处理，例如更新设备状态、位置等

    // 向发送方回复响应
    udp.beginPacket(udp.remoteIP(), udp.remotePort());
    udp.write(replyPacket);
    udp.endPacket();
  }
}
