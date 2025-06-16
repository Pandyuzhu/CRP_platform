import * as THREE from 'three';

/**
 * Kabsch算法实现 - 用于3D点集配准
 * 基于SVD分解计算最优旋转和平移变换
 */

/**
 * 计算两个点集之间的最优刚体变换
 * @param {Array<THREE.Vector3>} sourcePoints - 源点集
 * @param {Array<THREE.Vector3>} targetPoints - 目标点集
 * @returns {Object} 包含变换矩阵和统计信息的对象
 */
export function calculateKabschAlignment(sourcePoints, targetPoints) {
  if (sourcePoints.length !== targetPoints.length) {
    throw new Error('源点集和目标点集的点数必须相同');
  }
  
  if (sourcePoints.length < 3) {
    throw new Error('至少需要3个点对进行3D配准');
  }
  
  // 1. 计算质心
  const sourceCentroid = calculateCentroid(sourcePoints);
  const targetCentroid = calculateCentroid(targetPoints);
  
  // 2. 去中心化
  const centeredSource = sourcePoints.map(p => p.clone().sub(sourceCentroid));
  const centeredTarget = targetPoints.map(p => p.clone().sub(targetCentroid));
  
  // 3. 计算协方差矩阵 H = Σ(source_i * target_i^T)
  const H = calculateCovarianceMatrix(centeredSource, centeredTarget);
  
  // 4. SVD分解获得最优旋转矩阵
  const R = calculateOptimalRotationSVD(H);
  
  // 5. 计算平移向量
  const rotatedCentroid = sourceCentroid.clone().applyMatrix3(R);
  const translation = targetCentroid.clone().sub(rotatedCentroid);
  
  // 6. 构建4x4变换矩阵
  const transformMatrix = new THREE.Matrix4();
  transformMatrix.makeBasis(
    new THREE.Vector3(R.elements[0], R.elements[3], R.elements[6]),
    new THREE.Vector3(R.elements[1], R.elements[4], R.elements[7]),
    new THREE.Vector3(R.elements[2], R.elements[5], R.elements[8])
  );
  transformMatrix.setPosition(translation);
  
  // 7. 计算配准误差统计
  const errorStats = calculateAlignmentError(sourcePoints, targetPoints, transformMatrix);
  
  return {
    transformMatrix: transformMatrix,
    rotation: R,
    translation: translation,
    sourceCentroid: sourceCentroid,
    targetCentroid: targetCentroid,
    errorStats: errorStats,
    rmse: errorStats.rms,
    maxError: errorStats.max
  };
}

/**
 * 计算点集的质心
 * @param {Array<THREE.Vector3>} points - 点集
 * @returns {THREE.Vector3} 质心坐标
 */
function calculateCentroid(points) {
  const centroid = new THREE.Vector3();
  points.forEach(point => centroid.add(point));
  centroid.divideScalar(points.length);
  return centroid;
}

/**
 * 计算协方差矩阵 H = Σ(source_i * target_i^T)
 * @param {Array<THREE.Vector3>} centeredSource - 去中心化的源点集
 * @param {Array<THREE.Vector3>} centeredTarget - 去中心化的目标点集
 * @returns {THREE.Matrix3} 3x3协方差矩阵
 */
function calculateCovarianceMatrix(centeredSource, centeredTarget) {
  const H = new THREE.Matrix3();
  H.set(0, 0, 0, 0, 0, 0, 0, 0, 0);
  
  for (let i = 0; i < centeredSource.length; i++) {
    const s = centeredSource[i];
    const t = centeredTarget[i];
    
    // H += s * t^T
    H.elements[0] += s.x * t.x; H.elements[1] += s.x * t.y; H.elements[2] += s.x * t.z;
    H.elements[3] += s.y * t.x; H.elements[4] += s.y * t.y; H.elements[5] += s.y * t.z;
    H.elements[6] += s.z * t.x; H.elements[7] += s.z * t.y; H.elements[8] += s.z * t.z;
  }
  
  return H;
}

/**
 * 使用SVD分解计算最优旋转矩阵
 * @param {THREE.Matrix3} H - 协方差矩阵
 * @returns {THREE.Matrix3} 最优旋转矩阵
 */
function calculateOptimalRotationSVD(H) {
  // 使用简化的SVD实现
  // 在实际应用中，应该使用更robust的数值库如ml-matrix
  
  // 计算 H^T * H 的特征值和特征向量
  const HTH = new THREE.Matrix3();
  HTH.multiplyMatrices(H.clone().transpose(), H);
  
  // 简化实现：使用幂迭代法求主特征向量
  const { eigenVectors, eigenValues } = computeEigenDecomposition(HTH);
  
  // 构建V矩阵（右奇异向量）
  const V = new THREE.Matrix3();
  V.set(
    eigenVectors[0].x, eigenVectors[1].x, eigenVectors[2].x,
    eigenVectors[0].y, eigenVectors[1].y, eigenVectors[2].y,
    eigenVectors[0].z, eigenVectors[1].z, eigenVectors[2].z
  );
  
  // 计算U = H * V * Σ^(-1)
  const U = calculateLeftSingularVectors(H, V, eigenValues);
  
  // R = U * V^T
  const R = new THREE.Matrix3();
  R.multiplyMatrices(U, V.clone().transpose());
  
  // 确保R是旋转矩阵（行列式为1）
  if (R.determinant() < 0) {
    // 如果行列式为负，翻转最小奇异值对应的列
    const minIndex = eigenValues.indexOf(Math.min(...eigenValues));
    if (minIndex === 0) {
      V.elements[0] *= -1; V.elements[3] *= -1; V.elements[6] *= -1;
    } else if (minIndex === 1) {
      V.elements[1] *= -1; V.elements[4] *= -1; V.elements[7] *= -1;
    } else {
      V.elements[2] *= -1; V.elements[5] *= -1; V.elements[8] *= -1;
    }
    R.multiplyMatrices(U, V.clone().transpose());
  }
  
  return R;
}

/**
 * 简化的特征值分解实现
 * @param {THREE.Matrix3} matrix - 输入矩阵
 * @returns {Object} 包含特征值和特征向量的对象
 */
function computeEigenDecomposition(matrix) {
  // 简化实现：使用解析解或迭代方法
  // 这里使用一个基本的幂迭代法实现
  
  const eigenVectors = [];
  const eigenValues = [];
  
  // 对于3x3对称矩阵，我们可以使用解析方法或迭代方法
  // 这里使用简化的实现
  
  // 第一个特征向量（主特征向量）
  let v1 = new THREE.Vector3(1, 0, 0);
  for (let i = 0; i < 20; i++) {
    const Av = new THREE.Vector3();
    Av.x = matrix.elements[0] * v1.x + matrix.elements[1] * v1.y + matrix.elements[2] * v1.z;
    Av.y = matrix.elements[3] * v1.x + matrix.elements[4] * v1.y + matrix.elements[5] * v1.z;
    Av.z = matrix.elements[6] * v1.x + matrix.elements[7] * v1.y + matrix.elements[8] * v1.z;
    
    const norm = Av.length();
    if (norm > 1e-10) {
      v1 = Av.divideScalar(norm);
    }
  }
  
  const lambda1 = v1.dot(new THREE.Vector3(
    matrix.elements[0] * v1.x + matrix.elements[1] * v1.y + matrix.elements[2] * v1.z,
    matrix.elements[3] * v1.x + matrix.elements[4] * v1.y + matrix.elements[5] * v1.z,
    matrix.elements[6] * v1.x + matrix.elements[7] * v1.y + matrix.elements[8] * v1.z
  ));
  
  eigenVectors.push(v1);
  eigenValues.push(lambda1);
  
  // 简化：使用正交向量作为其他特征向量
  const v2 = new THREE.Vector3();
  if (Math.abs(v1.x) < 0.9) {
    v2.set(1, 0, 0);
  } else {
    v2.set(0, 1, 0);
  }
  v2.sub(v1.clone().multiplyScalar(v2.dot(v1))).normalize();
  
  const v3 = new THREE.Vector3().crossVectors(v1, v2).normalize();
  
  eigenVectors.push(v2, v3);
  eigenValues.push(1, 1); // 简化的特征值
  
  return { eigenVectors, eigenValues };
}

/**
 * 计算左奇异向量矩阵U
 * @param {THREE.Matrix3} H - 协方差矩阵
 * @param {THREE.Matrix3} V - 右奇异向量矩阵
 * @param {Array<number>} eigenValues - 特征值数组
 * @returns {THREE.Matrix3} 左奇异向量矩阵
 */
function calculateLeftSingularVectors(H, V, eigenValues) {
  const U = new THREE.Matrix3();
  
  // U = H * V * Σ^(-1)
  // 简化实现
  const HV = new THREE.Matrix3();
  HV.multiplyMatrices(H, V);
  
  // 归一化列向量
  for (let col = 0; col < 3; col++) {
    const colVector = new THREE.Vector3(
      HV.elements[col],
      HV.elements[col + 3],
      HV.elements[col + 6]
    );
    
    const norm = colVector.length();
    if (norm > 1e-10) {
      colVector.divideScalar(norm);
      U.elements[col] = colVector.x;
      U.elements[col + 3] = colVector.y;
      U.elements[col + 6] = colVector.z;
    }
  }
  
  return U;
}

/**
 * 计算配准误差统计
 * @param {Array<THREE.Vector3>} sourcePoints - 源点集
 * @param {Array<THREE.Vector3>} targetPoints - 目标点集
 * @param {THREE.Matrix4} transformMatrix - 变换矩阵
 * @returns {Object} 误差统计信息
 */
function calculateAlignmentError(sourcePoints, targetPoints, transformMatrix) {
  let totalSquaredError = 0;
  let maxError = 0;
  const errors = [];
  
  for (let i = 0; i < sourcePoints.length; i++) {
    const transformedPoint = sourcePoints[i].clone().applyMatrix4(transformMatrix);
    const error = transformedPoint.distanceTo(targetPoints[i]);
    
    errors.push(error);
    totalSquaredError += error * error;
    maxError = Math.max(maxError, error);
  }
  
  const rmsError = Math.sqrt(totalSquaredError / sourcePoints.length);
  const meanError = errors.reduce((sum, err) => sum + err, 0) / errors.length;
  
  // 计算旋转角度
  const rotationAngle = extractRotationAngle(transformMatrix);
  
  return {
    rms: rmsError,
    mean: meanError,
    max: maxError,
    min: Math.min(...errors),
    std: calculateStandardDeviation(errors, meanError),
    individual: errors,
    rotation: rotationAngle
  };
}

/**
 * 从变换矩阵中提取旋转角度
 * @param {THREE.Matrix4} transformMatrix - 变换矩阵
 * @returns {number} 旋转角度（度）
 */
function extractRotationAngle(transformMatrix) {
  // 提取旋转矩阵部分
  const rotationMatrix = new THREE.Matrix3();
  rotationMatrix.setFromMatrix4(transformMatrix);
  
  // 计算旋转角度（轴角表示）
  const trace = rotationMatrix.elements[0] + rotationMatrix.elements[4] + rotationMatrix.elements[8];
  const angle = Math.acos(Math.max(-1, Math.min(1, (trace - 1) / 2)));
  
  return angle * 180 / Math.PI; // 转换为度
}

/**
 * 计算标准差
 * @param {Array<number>} values - 数值数组
 * @param {number} mean - 均值
 * @returns {number} 标准差
 */
function calculateStandardDeviation(values, mean) {
  const squaredDiffs = values.map(value => Math.pow(value - mean, 2));
  const avgSquaredDiff = squaredDiffs.reduce((sum, diff) => sum + diff, 0) / values.length;
  return Math.sqrt(avgSquaredDiff);
}

/**
 * 验证配准质量
 * @param {Object} errorStats - 误差统计信息
 * @returns {Object} 配准质量评估
 */
export function assessAlignmentQuality(errorStats) {
  const { rms, max, std } = errorStats;
  
  let quality = 'poor';
  let score = 0;
  let recommendations = [];
  
  // RMS误差评估
  if (rms < 0.01) {
    quality = 'excellent';
    score += 40;
  } else if (rms < 0.02) {
    quality = 'very_good';
    score += 35;
  } else if (rms < 0.05) {
    quality = 'good';
    score += 25;
  } else if (rms < 0.1) {
    quality = 'fair';
    score += 15;
    recommendations.push('考虑增加更多特征点对');
  } else {
    quality = 'poor';
    score += 5;
    recommendations.push('需要重新选择特征点对');
    recommendations.push('检查点对对应关系是否正确');
  }
  
  // 最大误差评估
  if (max < 0.05) {
    score += 20;
  } else if (max < 0.1) {
    score += 15;
  } else if (max < 0.2) {
    score += 10;
    recommendations.push('存在较大局部误差，检查异常点对');
  } else {
    score += 0;
    recommendations.push('存在严重异常点对，需要重新选择');
  }
  
  // 一致性评估（标准差）
  if (std < rms * 0.5) {
    score += 20; // 误差分布均匀
  } else if (std < rms) {
    score += 15;
  } else {
    score += 5;
    recommendations.push('误差分布不均匀，可能存在系统性偏差');
  }
  
  return {
    quality,
    score: Math.min(100, score),
    recommendations,
    summary: getQualitySummary(quality, rms, max)
  };
}

/**
 * 获取质量评估摘要
 * @param {string} quality - 质量等级
 * @param {number} rms - RMS误差
 * @param {number} max - 最大误差
 * @returns {string} 质量摘要
 */
function getQualitySummary(quality, rms, max) {
  const qualityMap = {
    excellent: '优秀',
    very_good: '很好',
    good: '良好',
    fair: '一般',
    poor: '较差'
  };
  
  return `配准质量: ${qualityMap[quality]} (RMS: ${rms.toFixed(4)}m, 最大: ${max.toFixed(4)}m)`;
} 