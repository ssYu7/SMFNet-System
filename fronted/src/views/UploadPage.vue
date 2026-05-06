<template>
  <div class="upload-container">
    <h2>视听源分离 - 双流输入系统</h2>
    <el-alert
      title="请上传两个视频进行混合分离测试"
      type="info"
      show-icon
      :closable="false"
      style="margin-bottom: 20px;"
    />

    <el-card class="upload-card">
      <el-upload
        v-model:file-list="fileList"
        class="upload-demo"
        drag
        action="#"
        multiple
        :auto-upload="false"
        :limit="2"
        :on-exceed="handleExceed"
        :on-change="handleChange"
        accept=".mp4,.avi,.mov"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          拖拽 <strong>2个视频</strong> 到此处，或点击上传
        </div>
      </el-upload>

      <div class="action-area">
        <el-button
          type="primary"
          size="large"
          :loading="loading"
          @click="submitUpload"
          :disabled="fileList.length !== 2"
        >
          {{ loading ? '模型推理中 (约需几分钟)...' : '开始分离处理' }}
        </el-button>
      </div>
    </el-card>

    <div v-if="loading" class="progress-box">
      <p>正在执行分离任务，请耐心等待...</p>
      <el-progress :percentage="50" indeterminate />
    </div>

    <div v-if="resultUrls" class="result-section">
      <el-divider>可视化分析结果 (GT vs Pred)</el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">视频 1 分析结果</div>
            </template>

            <div class="compare-group">
              <h4>1. Amp (Map) 对比</h4>
              <el-row :gutter="10">
                <el-col :span="12">
                  <div class="sub-label">Ground Truth</div>
                  <el-image :src="getFullUrl(resultUrls.gtmap1)" :preview-src-list="[getFullUrl(resultUrls.gtmap1)]" fit="contain" class="result-img" />
                </el-col>
                <el-col :span="12">
                  <div class="sub-label">Prediction</div>
                  <el-image :src="getFullUrl(resultUrls.predmap1)" :preview-src-list="[getFullUrl(resultUrls.predmap1)]" fit="contain" class="result-img" />
                </el-col>
              </el-row>
            </div>

            <div class="compare-group">
              <h4>2. Mask 对比</h4>
              <el-row :gutter="10">
                <el-col :span="12">
                  <div class="sub-label">Ground Truth</div>
                  <el-image :src="getFullUrl(resultUrls.gtmask1)" :preview-src-list="[getFullUrl(resultUrls.gtmask1)]" fit="contain" class="result-img" />
                </el-col>
                <el-col :span="12">
                  <div class="sub-label">Prediction</div>
                  <el-image :src="getFullUrl(resultUrls.predmask1)" :preview-src-list="[getFullUrl(resultUrls.predmask1)]" fit="contain" class="result-img" />
                </el-col>
              </el-row>
            </div>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card shadow="hover">
            <template #header>
              <div class="card-header">视频 2 分析结果</div>
            </template>

            <div class="compare-group">
              <h4>1. Amp (Map) 对比</h4>
              <el-row :gutter="10">
                <el-col :span="12">
                  <div class="sub-label">Ground Truth</div>
                  <el-image :src="getFullUrl(resultUrls.gtmap2)" :preview-src-list="[getFullUrl(resultUrls.gtmap2)]" fit="contain" class="result-img" />
                </el-col>
                <el-col :span="12">
                  <div class="sub-label">Prediction</div>
                  <el-image :src="getFullUrl(resultUrls.predmap2)" :preview-src-list="[getFullUrl(resultUrls.predmap2)]" fit="contain" class="result-img" />
                </el-col>
              </el-row>
            </div>

            <div class="compare-group">
              <h4>2. Mask 对比</h4>
              <el-row :gutter="10">
                <el-col :span="12">
                  <div class="sub-label">Ground Truth</div>
                  <el-image :src="getFullUrl(resultUrls.gtmask2)" :preview-src-list="[getFullUrl(resultUrls.gtmask2)]" fit="contain" class="result-img" />
                </el-col>
                <el-col :span="12">
                  <div class="sub-label">Prediction</div>
                  <el-image :src="getFullUrl(resultUrls.predmask2)" :preview-src-list="[getFullUrl(resultUrls.predmask2)]" fit="contain" class="result-img" />
                </el-col>
              </el-row>
            </div>
          </el-card>
        </el-col>

      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import request from '@/api/request'
import { UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { BASE_URL } from '@/api/config'

const fileList = ref([])
const loading = ref(false)
const resultUrls = ref(null)

const handleExceed = () => {
  ElMessage.warning('限制只能上传 2 个视频！')
}

const handleChange = (uploadFile, uploadFiles) => {
  fileList.value = uploadFiles
}

const submitUpload = async () => {
  if (fileList.value.length !== 2) {
    ElMessage.error('请务必上传两个视频！')
    return
  }

  const formData = new FormData()
  formData.append('files', fileList.value[0].raw)
  formData.append('files', fileList.value[1].raw)
  formData.append('user_id', localStorage.getItem('user_id') || 1)

  loading.value = true
  resultUrls.value = null

  try {
    const res = await request.post('/api/upload_pair', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })

    if (res.data.status === 'success') {
      ElMessage.success('分离完成！')
      resultUrls.value = res.data.data.urls
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('处理失败，请检查服务连接')
  } finally {
    loading.value = false
  }
}

const getFullUrl = (path) => {
  if (!path) return ''
  const cleanPath = path.startsWith('/') ? path : '/' + path
  return `${BASE_URL}${cleanPath}`
}
</script>

<style scoped>
.upload-container { max-width: 1200px; margin: 0 auto; padding: 20px; } /* 稍微加宽容器 */
.upload-card { text-align: center; padding: 30px; }
.action-area { margin-top: 20px; }
.progress-box { margin-top: 30px; text-align: center; }
.result-section { margin-top: 40px; }

.compare-group { margin-bottom: 20px; }
.compare-group h4 { margin: 10px 0; color: #303133; font-size: 15px; border-left: 3px solid #409EFF; padding-left: 8px; }

.sub-label {
  text-align: center;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.result-img {
  width: 100%;
  height: 180px; /* 图片高度稍微调小一点，以便放下更多内容 */
  background-color: #f5f7fa;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}
.card-header { font-weight: bold; font-size: 16px; }
</style>
