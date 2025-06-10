import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { ref, onMounted, onBeforeUnmount } from 'vue';

/**
 * 提供Three.js相关功能的Hook
 * @returns {Object} Three.js相关的工具和状态
 */
export function useThreeJs() {
  const container = ref(null);
  const scene = ref(null);
  const camera = ref(null);
  const renderer = ref(null);
  const controls = ref(null);
  const isReady = ref(false);
  
  /**
   * 初始化Three.js场景
   * @param {HTMLElement} el 容器元素
   * @param {Object} options 配置选项
   * @returns {Object} 场景对象
   */
  function initScene(el, options = {}) {
    if (!el) return null;
    
    // 创建场景
    const newScene = new THREE.Scene();
    if (options.backgroundColor) {
      newScene.background = new THREE.Color(options.backgroundColor);
    }
    
    // 创建相机
    const aspect = el.clientWidth / el.clientHeight;
    const newCamera = new THREE.PerspectiveCamera(
      options.fov || 75, 
      aspect, 
      options.near || 0.1, 
      options.far || 1000
    );
    newCamera.position.set(
      options.cameraX || 5, 
      options.cameraY || 5, 
      options.cameraZ || 5
    );
    
    // 创建渲染器
    const newRenderer = new THREE.WebGLRenderer({ 
      antialias: options.antialias !== false,
      alpha: options.alpha === true
    });
    newRenderer.setSize(el.clientWidth, el.clientHeight);
    newRenderer.setPixelRatio(window.devicePixelRatio);
    el.appendChild(newRenderer.domElement);
    
    // 创建控制器
    const newControls = new OrbitControls(newCamera, newRenderer.domElement);
    newControls.enableDamping = options.enableDamping !== false;
    
    // 添加默认光源
    if (options.addDefaultLights !== false) {
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
      newScene.add(ambientLight);
      
      const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
      directionalLight.position.set(10, 10, 10);
      newScene.add(directionalLight);
    }
    
    // 添加网格和坐标轴
    if (options.addGrid !== false) {
      const gridHelper = new THREE.GridHelper(10, 10);
      newScene.add(gridHelper);
    }
    
    if (options.addAxes !== false) {
      const axesHelper = new THREE.AxesHelper(5);
      newScene.add(axesHelper);
    }
    
    // 设置引用
    scene.value = newScene;
    camera.value = newCamera;
    renderer.value = newRenderer;
    controls.value = newControls;
    container.value = el;
    isReady.value = true;
    
    // 窗口大小变化时重新调整
    const handleResize = () => {
      if (!container.value) return;
      camera.value.aspect = container.value.clientWidth / container.value.clientHeight;
      camera.value.updateProjectionMatrix();
      renderer.value.setSize(container.value.clientWidth, container.value.clientHeight);
    };
    
    window.addEventListener('resize', handleResize);
    
    // 动画循环
    let animationId = null;
    
    const animate = () => {
      animationId = requestAnimationFrame(animate);
      controls.value.update();
      renderer.value.render(scene.value, camera.value);
    };
    
    animate();
    
    // 返回清理函数
    const dispose = () => {
      window.removeEventListener('resize', handleResize);
      if (animationId) {
        cancelAnimationFrame(animationId);
      }
      if (renderer.value) {
        renderer.value.dispose();
        if (container.value && renderer.value.domElement) {
          container.value.removeChild(renderer.value.domElement);
        }
      }
      isReady.value = false;
    };
    
    return { 
      scene: newScene, 
      camera: newCamera, 
      renderer: newRenderer, 
      controls: newControls,
      dispose
    };
  }
  
  return {
    container,
    scene,
    camera,
    renderer,
    controls,
    isReady,
    initScene
  };
} 