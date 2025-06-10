<template>
  <div class="rtk-monitor-dashboard">
    <!-- 顶部状态栏 -->
    <div class="status-bar">
      <div class="status-item">
        <div class="status-icon online"></div>
        <span>系统在线</span>
      </div>
      <div class="status-item">
        <div class="status-icon" :class="wsConnected ? 'online' : 'offline'"></div>
        <span>{{ wsConnected ? 'WebSocket已连接' : 'WebSocket未连接' }}</span>
      </div>
      <div class="status-item">
        <div class="status-value">{{ Object.keys(rtkDevices).length }}</div>
        <span>在线设备</span>
      </div>
      <div class="status-item">
        <div class="status-value">{{ Object.values(rtkDevices).filter(d => d.isBaseStation).length }}</div>
        <span>基站数量</span>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧控制面板 -->
      <div class="control-panel">
        <div class="panel-section">
          <h3 class="section-title">设备扫描</h3>
          <div class="scan-controls">
            <el-button 
              type="primary" 
              class="scan-btn"
              @click="scanRtkDevices" 
              :loading="isScanning"
              :disabled="isScanning"
            >
              <i class="el-icon-search"></i>
              {{ isScanning ? '扫描中...' : '扫描RTK设备' }}
            </el-button>
          </div>
          
          <!-- 扫描结果 -->
          <div v-if="scanResults.length > 0" class="scan-results">
            <h4>发现的设备</h4>
            <div class="device-grid">
              <div v-for="device in scanResults" :key="device.id" class="device-card" @click="showConfigDialog(device)">
                <div class="device-icon">
                  <i class="el-icon-position"></i>
                </div>
                <div class="device-info">
                  <div class="device-id">{{ device.id }}</div>
                  <div class="device-ip">{{ device.ip }}</div>
                </div>
                <div class="device-signal">
                  <div class="signal-bars">
                    <div class="bar active"></div>
                    <div class="bar active"></div>
                    <div class="bar active"></div>
                    <div class="bar"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 已注册设备 -->
        <div class="panel-section">
          <h3 class="section-title">已注册设备</h3>
          <div class="registered-devices">
            <div v-for="device in Object.values(rtkDevices)" :key="device.id" 
                 class="registered-device" 
                 :class="{ active: device.connected }"
                 @click="editDevice(device)">
              <div class="device-header">
                <div class="device-name">{{ device.name || device.id }}</div>
                <div class="device-status" :class="device.connected ? 'online' : 'offline'">
                  {{ device.connected ? '在线' : '离线' }}
                </div>
              </div>
              <div class="device-details">
                <div class="detail-item">
                  <span class="label">IP:</span>
                  <span class="value">{{ device.ip }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">类型:</span>
                  <span class="value" :class="device.isBaseStation ? 'base-station' : 'mobile-station'">
                    {{ device.isBaseStation ? '基站' : '移动站' }}
                  </span>
                </div>
                <div class="detail-item">
                  <span class="label">编号:</span>
                  <span class="value">{{ device.deviceNumber || '-' }}</span>
                </div>
              </div>
              <div v-if="device.connected && device.data" class="position-data">
                <div class="coordinate">
                  <span class="coord-label">E:</span>
                  <span class="coord-value">{{ device.data.e?.toFixed(3) }}m</span>
                </div>
                <div class="coordinate">
                  <span class="coord-label">N:</span>
                  <span class="coord-value">{{ device.data.n?.toFixed(3) }}m</span>
                </div>
                <div class="coordinate">
                  <span class="coord-label">U:</span>
                  <span class="coord-value">{{ device.data.u?.toFixed(3) }}m</span>
                </div>
              </div>
              <!-- 可视化控制 -->
              <div class="visualization-control">
                <el-switch 
                  v-model="device.showIn3D" 
                  size="small"
                  active-text="3D显示" 
                  inactive-text="隐藏"
                  :active-value="true"
                  :inactive-value="false"
                  @change="(value) => toggleVisualization(device.id, value)"
                  @click.stop
                />
              </div>
              <!-- 轨迹控制按钮 -->
              <div v-if="device.connected" class="trajectory-controls">
                <el-button 
                  size="small" 
                  :type="device.recording ? 'danger' : 'success'"
                  @click="toggleRecording(device.id)"
                  class="trajectory-btn"
                >
                  {{ device.recording ? '停止记录' : '开始记录' }}
                </el-button>
                <el-button 
                  size="small" 
                  type="info"
                  @click="clearTrajectory(device.id)"
                  class="trajectory-btn"
                >
                  清除轨迹
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧3D可视化 -->
      <div class="visualization-panel">
        <div class="panel-header">
          <h2>3D可视化</h2>
        </div>
                 <div ref="container3d" class="three-container"></div>
      </div>
    </div>

    <!-- 设备配置对话框 -->
    <el-dialog
      v-model="configDialogVisible"
      title="RTK设备配置"
      width="500px"
      class="config-dialog"
      :close-on-click-modal="false"
    >
      <el-form :model="configForm" :rules="configRules" ref="configFormRef" label-width="100px">
        <el-form-item label="设备ID" prop="deviceId">
          <el-input v-model="configForm.deviceId" :disabled="isEditing" />
        </el-form-item>
        <el-form-item label="设备名称" prop="name">
          <el-input v-model="configForm.name" placeholder="请输入设备名称" />
        </el-form-item>
        <el-form-item label="IP地址" prop="ip">
          <el-input v-model="configForm.ip" :disabled="isEditing" />
        </el-form-item>
        <el-form-item label="设备编号" prop="deviceNumber">
          <el-input v-model="configForm.deviceNumber" placeholder="请输入设备编号" />
        </el-form-item>
        <el-form-item label="设备类型">
          <el-radio-group v-model="configForm.isBaseStation">
            <el-radio :value="false">移动站</el-radio>
            <el-radio :value="true">基站</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="3D可视化">
          <el-switch 
            v-model="configForm.showIn3D" 
            active-text="显示" 
            inactive-text="隐藏"
            :active-value="true"
            :inactive-value="false"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="configDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveDeviceConfig" :loading="isSaving">
            {{ isEditing ? '保存' : '添加' }}
          </el-button>
          <el-button 
            v-if="isEditing" 
            type="danger" 
            @click="deleteDevice"
          >
            删除设备
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, computed, nextTick, markRaw } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import axios from 'axios';
import { apiBaseUrl } from '@/config';

// 数据状态
const rtkDevices = ref({});
const scanResults = ref([]);
const isScanning = ref(false);
const wsConnected = ref(false);
const is3dViewReady = ref(false);
const container3d = ref(null);
const showGrid = ref(true);

// 场景状态
const scene = ref(null);
const camera = ref(null);
const renderer = ref(null);
const controls = ref(null);
const deviceMeshes = ref({});
const baseMeshes = ref([]);
const gridHelper = ref(null);
const trajectoryLines = ref({});
const trajectoryPoints = ref({});

// 配置对话框状态
const configDialogVisible = ref(false);
const isEditing = ref(false);
const isSaving = ref(false);
const configFormRef = ref(null);
const configForm = ref({
  deviceId: '',
  name: '',
  ip: '',
  deviceNumber: '',
  isBaseStation: false,
  showIn3D: true
});

const configRules = {
  deviceId: [
    { required: true, message: '请输入设备ID', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入设备名称', trigger: 'blur' }
  ],
  ip: [
    { required: true, message: '请输入IP地址', trigger: 'blur' },
    { pattern: /^(\d{1,3}\.){3}\d{1,3}$/, message: 'IP地址格式不正确', trigger: 'blur' }
  ],
  deviceNumber: [
    { required: true, message: '请输入设备编号', trigger: 'blur' }
  ]
};

// 刷新间隔
const refreshInterval = ref(null);

// 初始化3D场景
function init3DScene() {
  if (!container3d.value) return;
  
  // 创建场景
  scene.value = markRaw(new THREE.Scene());
  scene.value.background = new THREE.Color(0x000000);
  
  // 创建相机
  camera.value = markRaw(new THREE.PerspectiveCamera(
    75, 
    container3d.value.clientWidth / container3d.value.clientHeight, 
    0.1, 
    1000
  ));
  camera.value.position.set(15, 15, 15);
  camera.value.lookAt(0, 0, 0);
  
  // 创建渲染器
  renderer.value = markRaw(new THREE.WebGLRenderer({ antialias: true }));
  renderer.value.setSize(container3d.value.clientWidth, container3d.value.clientHeight);
  renderer.value.shadowMap.enabled = true;
  renderer.value.shadowMap.type = THREE.PCFSoftShadowMap;
  container3d.value.appendChild(renderer.value.domElement);
  
  // 创建轨道控制器
  controls.value = markRaw(new OrbitControls(camera.value, renderer.value.domElement));
  controls.value.enableDamping = true;
  controls.value.dampingFactor = 0.05;
  controls.value.target.set(0, 0, 0);
  controls.value.minDistance = 5;
  controls.value.maxDistance = 100;
  
  // 添加网格
  gridHelper.value = markRaw(new THREE.GridHelper(20, 20, 0xffffff, 0x333333));
  gridHelper.value.material.transparent = true;
  gridHelper.value.material.opacity = 0.3;
  scene.value.add(gridHelper.value);
  
  // 添加坐标轴 - 缩小尺寸
  const axesHelper = markRaw(new THREE.AxesHelper(2));
  scene.value.add(axesHelper);
  
  // 添加坐标轴标签 (E, N, U)
  // 创建文本几何体的函数
  function createAxisLabel(text, position, color) {
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 32;
    const ctx = canvas.getContext('2d');
    
    ctx.fillStyle = color;
    ctx.font = 'bold 20px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, 32, 16);
    
    const texture = markRaw(new THREE.CanvasTexture(canvas));
    const spriteMaterial = markRaw(new THREE.SpriteMaterial({ map: texture }));
    const sprite = markRaw(new THREE.Sprite(spriteMaterial));
    sprite.scale.set(0.5, 0.25, 1);
    sprite.position.copy(position);
    
    return sprite;
  }
  
  // 添加E、N、U标签
  const eLabel = createAxisLabel('E', new THREE.Vector3(2.5, 0, 0), '#ff0000');
  const nLabel = createAxisLabel('N', new THREE.Vector3(0, 0, 2.5), '#00ff00');
  const uLabel = createAxisLabel('U', new THREE.Vector3(0, 2.5, 0), '#0000ff');
  
  scene.value.add(eLabel);
  scene.value.add(nLabel);
  scene.value.add(uLabel);
  
  // 添加光源
  const ambientLight = markRaw(new THREE.AmbientLight(0x404040, 0.3));
  scene.value.add(ambientLight);
  
  const directionalLight = markRaw(new THREE.DirectionalLight(0xffffff, 0.8));
  directionalLight.position.set(20, 20, 20);
  directionalLight.castShadow = true;
  directionalLight.shadow.mapSize.width = 2048;
  directionalLight.shadow.mapSize.height = 2048;
  scene.value.add(directionalLight);
  
  // 动画循环
  function animate() {
    requestAnimationFrame(animate);
    controls.value.update();
    renderer.value.render(scene.value, camera.value);
  }
  
  animate();
  is3dViewReady.value = true;
  
  // 窗口大小变化处理
  function handleResize() {
    if (!container3d.value) return;
    camera.value.aspect = container3d.value.clientWidth / container3d.value.clientHeight;
    camera.value.updateProjectionMatrix();
    renderer.value.setSize(container3d.value.clientWidth, container3d.value.clientHeight);
  }
  
  window.addEventListener('resize', handleResize);
  
  onBeforeUnmount(() => {
    window.removeEventListener('resize', handleResize);
    if (renderer.value) {
      renderer.value.dispose();
      container3d.value.removeChild(renderer.value.domElement);
    }
  });
}

// 更新3D场景中的设备
function updateDevicesIn3D() {
  if (!scene.value) {
    console.log('3D场景未初始化');
    return;
  }
  
  console.log('开始更新3D场景，设备数量:', Object.keys(rtkDevices.value).length);
  
  // 清除旧的设备模型
  Object.values(deviceMeshes.value).forEach(mesh => {
    scene.value.remove(mesh);
  });
  baseMeshes.value.forEach(mesh => {
    scene.value.remove(mesh);
  });
  
  deviceMeshes.value = {};
  baseMeshes.value = [];
  
  // 不清除轨迹线，保持轨迹显示
  
  let visibleDeviceCount = 0;
  
  // 创建新的设备模型
  Object.values(rtkDevices.value).forEach(device => {
    console.log(`检查设备 ${device.id}:`, {
      connected: device.connected,
      hasData: !!device.data,
      showIn3D: device.showIn3D,
      data: device.data
    });
    
    // 只显示已连接、有数据且启用3D可视化的设备
    if (!device.connected || !device.data || !device.showIn3D) {
      console.log(`设备 ${device.id} 被跳过`);
      return;
    }
    
    visibleDeviceCount++;
    
    const position = markRaw(new THREE.Vector3(
      device.data.e || 0,
      device.data.u || 0,
      device.data.n || 0
    ));
    
    let geometry, material;
    
    if (device.isBaseStation) {
       // 基站：白色球体
       geometry = markRaw(new THREE.SphereGeometry(0.3, 16, 16));
       material = markRaw(new THREE.MeshLambertMaterial({ 
         color: 0xffffff,
         emissive: 0x222222
       }));
       
       // 基站覆盖范围
       const rangeGeometry = markRaw(new THREE.RingGeometry(4.5, 5, 32));
       const rangeMaterial = markRaw(new THREE.MeshBasicMaterial({ 
         color: 0xffffff, 
         transparent: true, 
         opacity: 0.1,
         side: THREE.DoubleSide
       }));
       const rangeMesh = markRaw(new THREE.Mesh(rangeGeometry, rangeMaterial));
       rangeMesh.rotation.x = -Math.PI / 2;
       rangeMesh.position.copy(position);
       rangeMesh.position.y = 0.01;
       scene.value.add(rangeMesh);
       baseMeshes.value.push(rangeMesh);
     } else {
       // 移动站：绿色球体
       geometry = markRaw(new THREE.SphereGeometry(0.2, 16, 16));
       material = markRaw(new THREE.MeshLambertMaterial({ 
         color: 0x00ff88,
         emissive: 0x002211
       }));
     }
    
    const mesh = markRaw(new THREE.Mesh(geometry, material));
    mesh.position.copy(position);
    mesh.castShadow = true;
    mesh.receiveShadow = true;
    
    // 添加设备标签
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    
    // 绘制背景
    ctx.fillStyle = 'rgba(0, 0, 0, 0.8)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
         // 绘制边框
     ctx.strokeStyle = device.isBaseStation ? '#ffffff' : '#00ff88';
     ctx.lineWidth = 2;
     ctx.strokeRect(2, 2, canvas.width - 4, canvas.height - 4);
    
    // 绘制文字
    ctx.fillStyle = 'white';
    ctx.font = 'bold 18px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(device.name || device.id, canvas.width / 2, canvas.height / 2);
    
    const texture = markRaw(new THREE.CanvasTexture(canvas));
    const spriteMaterial = markRaw(new THREE.SpriteMaterial({ map: texture }));
    const sprite = markRaw(new THREE.Sprite(spriteMaterial));
    sprite.scale.set(2, 0.5, 1);
    sprite.position.set(0, 0.8, 0);
    mesh.add(sprite);
    
    scene.value.add(mesh);
    deviceMeshes.value[device.id] = mesh;
    
    console.log(`已添加设备 ${device.id} 到3D场景，位置:`, position);
    
    // 更新轨迹
    updateDeviceTrajectory(device);
  });
  
  console.log(`3D场景更新完成，可见设备数量: ${visibleDeviceCount}`);
}

// 更新设备轨迹
function updateDeviceTrajectory(device) {
  if (!device.connected || !device.data || !device.recording) return;
  
  const deviceId = device.id;
  const currentPosition = new THREE.Vector3(
    device.data.e || 0,
    device.data.u || 0,
    device.data.n || 0
  );
  
  // 初始化轨迹点数组
  if (!trajectoryPoints.value[deviceId]) {
    trajectoryPoints.value[deviceId] = [];
  }
  
  // 添加新的轨迹点（避免重复添加相同位置）
  const points = trajectoryPoints.value[deviceId];
  const lastPoint = points.length > 0 ? points[points.length - 1] : null;
  
  if (!lastPoint || lastPoint.distanceTo(currentPosition) > 0.01) {
    points.push(currentPosition.clone());
    
    // 限制轨迹点数量，避免内存过多占用
    if (points.length > 1000) {
      points.shift();
    }
    
    // 更新轨迹线
    updateTrajectoryLine(deviceId, points, device.isBaseStation);
  }
}

// 更新轨迹线
function updateTrajectoryLine(deviceId, points, isBaseStation) {
  if (points.length < 2) return;
  
  // 移除旧的轨迹线
  if (trajectoryLines.value[deviceId]) {
    scene.value.remove(trajectoryLines.value[deviceId]);
  }
  
  // 创建新的轨迹线
  const geometry = markRaw(new THREE.BufferGeometry().setFromPoints(points));
  const material = markRaw(new THREE.LineBasicMaterial({
    color: isBaseStation ? 0xffffff : 0x00ff88,
    linewidth: 2,
    transparent: true,
    opacity: 0.8
  }));
  
  const line = markRaw(new THREE.Line(geometry, material));
  scene.value.add(line);
  trajectoryLines.value[deviceId] = line;
}

// 获取所有RTK设备
async function fetchRtkDevices() {
  try {
    const response = await axios.get(`${apiBaseUrl}/api/rtk/devices`);
    if (response.data) {
      // 确保每个设备都有showIn3D属性
      Object.values(response.data).forEach(device => {
        if (device.showIn3D === undefined) {
          device.showIn3D = true; // 默认显示
        }
      });
      
      rtkDevices.value = response.data;
      
      console.log('已获取RTK设备:', Object.keys(rtkDevices.value));
      console.log('设备详情:', rtkDevices.value);
      
      if (is3dViewReady.value) {
        updateDevicesIn3D();
      }
    }
  } catch (error) {
    console.error('获取RTK设备失败:', error);
  }
}

// 扫描RTK设备
async function scanRtkDevices() {
  if (isScanning.value) return;
  
  isScanning.value = true;
  ElMessage.info('开始扫描RTK设备...');
  
  try {
    const response = await axios.post(`${apiBaseUrl}/api/rtk/scan`);
    
    if (response.data && response.data.success) {
      scanResults.value = response.data.devices || [];
      console.log('扫描到的设备:', scanResults.value);
      
      if (scanResults.value.length === 0) {
        ElMessage.info('未发现新的RTK设备');
      } else {
        ElMessage.success(`发现 ${scanResults.value.length} 个RTK设备`);
      }
    }
  } catch (error) {
    console.error('扫描RTK设备失败:', error);
    ElMessage.error('扫描RTK设备失败');
  } finally {
    isScanning.value = false;
  }
}

// 显示配置对话框
function showConfigDialog(device) {
  console.log('显示配置对话框，设备:', device);
  configForm.value = {
    deviceId: device.id,
    name: device.name || device.id,
    ip: device.ip,
    deviceNumber: '1',
    isBaseStation: false,
    showIn3D: true
  };
  isEditing.value = false;
  configDialogVisible.value = true;
}

// 编辑设备
function editDevice(device) {
  configForm.value = {
    deviceId: device.id,
    name: device.name || device.id,
    ip: device.ip,
    deviceNumber: device.deviceNumber || '1',
    isBaseStation: device.isBaseStation || false,
    showIn3D: device.showIn3D !== undefined ? device.showIn3D : true
  };
  isEditing.value = true;
  configDialogVisible.value = true;
}

// 保存设备配置
async function saveDeviceConfig() {
  if (!configFormRef.value) return;
  
  try {
    await configFormRef.value.validate();
    isSaving.value = true;
    
    const url = isEditing.value 
      ? `${apiBaseUrl}/api/rtk/devices/${configForm.value.deviceId}`
      : `${apiBaseUrl}/api/rtk/devices`;
    
    const method = isEditing.value ? 'put' : 'post';
    
    const requestData = {
      device_id: configForm.value.deviceId,
      ip_address: configForm.value.ip,
      name: configForm.value.name,
      device_number: configForm.value.deviceNumber,
      is_base_station: configForm.value.isBaseStation,
      show_in_3d: configForm.value.showIn3D
    };
    
    console.log('发送设备配置请求:', method, url, requestData);
    const response = await axios[method](url, requestData);
    
    if (response.data && response.data.success) {
      ElMessage.success(isEditing.value ? '设备更新成功' : '设备添加成功');
      configDialogVisible.value = false;
      
      // 从扫描结果中移除
      if (!isEditing.value) {
        scanResults.value = scanResults.value.filter(d => d.id !== configForm.value.deviceId);
      }
      
      await fetchRtkDevices();
    } else {
      ElMessage.error(isEditing.value ? '设备更新失败' : '设备添加失败');
    }
  } catch (error) {
    if (error !== 'validation failed') {
      console.error('保存设备配置失败:', error);
      ElMessage.error('操作失败');
    }
  } finally {
    isSaving.value = false;
  }
}

// 删除设备
async function deleteDevice() {
  try {
    await ElMessageBox.confirm('确定要删除此设备吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    const response = await axios.delete(`${apiBaseUrl}/api/rtk/devices/${configForm.value.deviceId}`);
    
    if (response.data && response.data.success) {
      ElMessage.success('设备删除成功');
      configDialogVisible.value = false;
      await fetchRtkDevices();
    } else {
      ElMessage.error('设备删除失败');
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除设备失败:', error);
      ElMessage.error('删除设备失败');
    }
  }
}

// 轨迹记录相关功能
async function toggleRecording(deviceId) {
  try {
    const device = rtkDevices.value[deviceId];
    if (!device) return;
    
    const action = device.recording ? 'stop' : 'start';
    const response = await axios.post(`${apiBaseUrl}/api/rtk/devices/${deviceId}/recording/${action}`);
    
    if (response.data && response.data.success) {
      ElMessage.success(device.recording ? '停止记录轨迹' : '开始记录轨迹');
      await fetchRtkDevices();
    } else {
      ElMessage.error('轨迹记录操作失败');
    }
  } catch (error) {
    console.error('轨迹记录操作失败:', error);
    ElMessage.error('轨迹记录操作失败');
  }
}

async function clearTrajectory(deviceId) {
  try {
    await ElMessageBox.confirm('确定要清除此设备的轨迹记录吗？', '确认清除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });
    
    const response = await axios.delete(`${apiBaseUrl}/api/rtk/devices/${deviceId}/records`);
    
    if (response.data && response.data.success) {
      ElMessage.success('轨迹记录已清除');
      // 清除3D场景中的轨迹线
      if (trajectoryLines.value[deviceId]) {
        scene.value.remove(trajectoryLines.value[deviceId]);
        delete trajectoryLines.value[deviceId];
      }
      if (trajectoryPoints.value[deviceId]) {
        trajectoryPoints.value[deviceId] = [];
      }
    } else {
      ElMessage.error('清除轨迹记录失败');
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清除轨迹记录失败:', error);
      ElMessage.error('清除轨迹记录失败');
    }
  }
}

// 切换设备3D可视化
async function toggleVisualization(deviceId, showIn3D) {
  try {
    const device = rtkDevices.value[deviceId];
    if (!device) return;
    
    console.log(`切换设备 ${deviceId} 的3D可视化为: ${showIn3D}`);
    
    // 先更新本地状态
    device.showIn3D = showIn3D;
    
    // 立即更新3D场景
    if (is3dViewReady.value) {
      updateDevicesIn3D();
    }
    
    // 然后更新后端
    const response = await axios.put(`${apiBaseUrl}/api/rtk/devices/${deviceId}`, {
      device_id: deviceId,
      ip_address: device.ip,
      name: device.name,
      device_number: device.deviceNumber,
      is_base_station: device.isBaseStation,
      show_in_3d: showIn3D
    });
    
    if (response.data && response.data.success) {
      ElMessage.success(showIn3D ? '已启用3D显示' : '已隐藏3D显示');
    } else {
      ElMessage.error('更新可视化设置失败，但本地显示已更新');
    }
  } catch (error) {
    console.error('切换可视化失败:', error);
    ElMessage.error('更新服务器失败，但本地显示已更新');
  }
}



// 生命周期钩子
onMounted(async () => {
  await fetchRtkDevices();
  
  nextTick(() => {
    init3DScene();
    
    // 如果没有设备，添加测试数据
    setTimeout(() => {
      if (Object.keys(rtkDevices.value).length === 0) {
        console.log('添加测试设备数据');
        rtkDevices.value = {
          'test_device': {
            id: 'test_device',
            name: '测试设备',
            ip: '192.168.1.100',
            connected: true,
            isBaseStation: false,
            showIn3D: true,
            data: {
              e: 5.0,
              n: 3.0,
              u: 1.0,
              timestamp: Date.now()
            }
          }
        };
        updateDevicesIn3D();
      }
    }, 3000);
  });
  
  refreshInterval.value = setInterval(fetchRtkDevices, 2000);
  
  // 模拟WebSocket连接状态
  setTimeout(() => {
    wsConnected.value = true;
  }, 1000);
});

onBeforeUnmount(() => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value);
  }
});
</script>

<style scoped>
.rtk-monitor-dashboard {
  min-height: 100vh;
  background: #000000;
  color: #ffffff;
  font-family: 'Roboto', sans-serif;
}

.status-bar {
  display: flex;
  justify-content: space-around;
  padding: 15px 30px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 2px 20px rgba(255, 255, 255, 0.1);
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}

.status-icon {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 0 10px currentColor;
}

.status-icon.online {
  background: #00ff88;
  color: #00ff88;
}

.status-icon.offline {
  background: #ff4444;
  color: #ff4444;
}

.status-value {
  font-size: 24px;
  font-weight: bold;
  color: #ffffff;
  text-shadow: 0 0 10px #ffffff;
}

.main-content {
  display: flex;
  gap: 20px;
  padding: 20px;
  height: calc(100vh - 80px);
}

.control-panel {
  width: 400px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.panel-section {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  padding: 20px;
  box-shadow: 0 8px 32px rgba(255, 255, 255, 0.1);
}

.section-title {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: #ffffff;
  text-shadow: 0 0 10px #ffffff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
  padding-bottom: 10px;
}

.scan-btn {
  width: 100%;
  height: 50px;
  background: linear-gradient(45deg, #444444, #666666);
  border: 1px solid #ffffff;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  color: #ffffff;
  box-shadow: 0 4px 20px rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.scan-btn:hover {
  background: linear-gradient(45deg, #666666, #888888);
  box-shadow: 0 6px 30px rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
}

.device-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.device-card {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  user-select: none;
}

.device-card:hover {
  background: rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 20px rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.device-card:active {
  transform: translateY(0px);
  background: rgba(255, 255, 255, 0.3);
}

.device-icon {
  font-size: 24px;
  color: #ffffff;
}

.device-info {
  flex: 1;
}

.device-id {
  font-weight: bold;
  color: #ffffff;
}

.device-ip {
  font-size: 12px;
  color: #888;
}

.signal-bars {
  display: flex;
  gap: 2px;
  align-items: end;
}

.bar {
  width: 4px;
  height: 8px;
  background: #333;
  border-radius: 2px;
}

.bar.active {
  background: #00ff88;
  box-shadow: 0 0 5px #00ff88;
}

.registered-devices {
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-height: 400px;
  overflow-y: auto;
}

.registered-device {
  padding: 15px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  user-select: none;
}

.registered-device:hover {
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1);
}

.registered-device:active {
  transform: scale(0.98);
  background: rgba(255, 255, 255, 0.15);
}

.registered-device.active {
  border-color: rgba(0, 255, 136, 0.5);
  box-shadow: 0 0 20px rgba(0, 255, 136, 0.2);
}

.device-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.device-name {
  font-weight: bold;
  color: #ffffff;
}

.device-status {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
}

.device-status.online {
  background: rgba(0, 255, 136, 0.2);
  color: #00ff88;
}

.device-status.offline {
  background: rgba(255, 68, 68, 0.2);
  color: #ff4444;
}

.device-details {
  display: flex;
  flex-direction: column;
  gap: 5px;
  margin-bottom: 10px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.label {
  color: #888;
}

.value {
  color: #ffffff;
}

.value.base-station {
  color: #ff6666;
}

.value.mobile-station {
  color: #66aaff;
}

.position-data {
  display: flex;
  gap: 15px;
  font-size: 11px;
}

.coordinate {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.coord-label {
  color: #888;
}

.coord-value {
  color: #ffffff;
  font-weight: bold;
}

.visualization-control {
  display: flex;
  justify-content: center;
  margin-top: 8px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.trajectory-controls {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  justify-content: center;
}

.trajectory-btn {
  font-size: 11px;
  padding: 4px 8px;
  height: auto;
  min-height: 24px;
}

.visualization-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.panel-header h2 {
  margin: 0;
  color: #ffffff;
  text-shadow: 0 0 10px #ffffff;
}



.three-container {
  flex: 1;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(255, 255, 255, 0.1);
}



:deep(.config-dialog) {
  background: rgba(240, 240, 240, 0.98);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(200, 200, 200, 0.5);
  border-radius: 15px;
}

:deep(.config-dialog .el-dialog__header) {
  background: linear-gradient(45deg, rgba(255, 255, 255, 0.9), rgba(240, 240, 240, 0.9));
  border-bottom: 1px solid rgba(200, 200, 200, 0.5);
}

:deep(.config-dialog .el-dialog__title) {
  color: #333333;
  font-weight: bold;
}

:deep(.config-dialog .el-form-item__label) {
  color: #333333;
  font-weight: 500;
}

:deep(.config-dialog .el-input__wrapper) {
  background: #ffffff;
  border: 1px solid #d1d5db;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

:deep(.config-dialog .el-input__inner) {
  background: transparent;
  border: none;
  color: #333333;
}

:deep(.config-dialog .el-input__inner::placeholder) {
  color: #9ca3af;
}

:deep(.config-dialog .el-radio__label) {
  color: #333333;
}

:deep(.config-dialog .el-radio__input.is-checked .el-radio__inner) {
  background-color: #409eff;
  border-color: #409eff;
}

:deep(.config-dialog .el-button--primary) {
  background-color: #409eff;
  border-color: #409eff;
}

:deep(.config-dialog .el-button--danger) {
  background-color: #f56565;
  border-color: #f56565;
}

/* 滚动条样式 */
.registered-devices::-webkit-scrollbar {
  width: 6px;
}

.registered-devices::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
}

.registered-devices::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 3px;
}

.registered-devices::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
}
</style>
