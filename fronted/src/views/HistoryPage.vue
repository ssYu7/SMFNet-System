<template>
  <div class="history-container">
    <h2>处理历史记录</h2>
    <el-table :data="tableData" stripe style="width: 100%" v-loading="loading">
      <el-table-column prop="created_at" label="处理时间" width="180">
        <template #default="scope">
          {{ formatTime(scope.row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column prop="video_name" label="视频源文件" />
      <el-table-column prop="result_path" label="结果文件夹" width="220" show-overflow-tooltip />

      <el-table-column label="操作" width="120">
        <template #default="scope">
          <el-button link type="primary" size="small" @click="viewResult(scope.row)">
            查看结果
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" title="分离结果详情 (GT vs Pred)" width="80%">
      <div v-if="currentResult">
        <el-row :gutter="20">

          <el-col :span="12">
            <el-card shadow="never">
              <template #header><strong>视频 1</strong></template>

              <div class="row-group">
                <p class="group-title">1. Amp (Map)</p>
                <el-row :gutter="10">
                  <el-col :span="12">
                    <span class="tag">GT</span>
                    <el-image :src="currentResult.gtmap1" fit="contain" class="mini-img"/>
                  </el-col>
                  <el-col :span="12">
                    <span class="tag">Pred</span>
                    <el-image :src="currentResult.predmap1" fit="contain" class="mini-img"/>
                  </el-col>
                </el-row>
              </div>

              <div class="row-group">
                <p class="group-title">2. Mask</p>
                <el-row :gutter="10">
                  <el-col :span="12">
                    <span class="tag">GT</span>
                    <el-image :src="currentResult.gtmask1" fit="contain" class="mini-img"/>
                  </el-col>
                  <el-col :span="12">
                    <span class="tag">Pred</span>
                    <el-image :src="currentResult.predmask1" fit="contain" class="mini-img"/>
                  </el-col>
                </el-row>
              </div>
            </el-card>
          </el-col>

          <el-col :span="12">
            <el-card shadow="never">
              <template #header><strong>视频 2</strong></template>

              <div class="row-group">
                <p class="group-title">1. Amp (Map)</p>
                <el-row :gutter="10">
                  <el-col :span="12">
                    <span class="tag">GT</span>
                    <el-image :src="currentResult.gtmap2" fit="contain" class="mini-img"/>
                  </el-col>
                  <el-col :span="12">
                    <span class="tag">Pred</span>
                    <el-image :src="currentResult.predmap2" fit="contain" class="mini-img"/>
                  </el-col>
                </el-row>
              </div>

              <div class="row-group">
                <p class="group-title">2. Mask</p>
                <el-row :gutter="10">
                  <el-col :span="12">
                    <span class="tag">GT</span>
                    <el-image :src="currentResult.gtmask2" fit="contain" class="mini-img"/>
                  </el-col>
                  <el-col :span="12">
                    <span class="tag">Pred</span>
                    <el-image :src="currentResult.predmask2" fit="contain" class="mini-img"/>
                  </el-col>
                </el-row>
              </div>
            </el-card>
          </el-col>

        </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import request from '@/api/request'
import { BASE_URL } from '@/api/config'

const tableData = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const currentResult = ref(null)

const fetchData = async () => {
  loading.value = true
  const uid = localStorage.getItem('user_id')
  try {
    const res = await request.get('/api/history', { params: { user_id: uid } })
    tableData.value = res.data
  } finally {
    loading.value = false
  }
}

const viewResult = (row) => {
  const folder = row.result_path
  if (!folder) {
    alert("该记录没有结果文件夹信息")
    return
  }

  // 手动拼接所有 URL
  const safeFolder = encodeURIComponent(folder)
  const baseUrl = `${BASE_URL}/viz/${safeFolder}`

  currentResult.value = {
    gtmap1:    `${baseUrl}/gtamp1.jpg`,
    predmap1:  `${baseUrl}/predamp1.jpg`,
    gtmap2:    `${baseUrl}/gtamp2.jpg`,
    predmap2:  `${baseUrl}/predamp2.jpg`,

    gtmask1:   `${baseUrl}/gtmask1.jpg`,
    predmask1: `${baseUrl}/predmask1.jpg`,
    gtmask2:   `${baseUrl}/gtmask2.jpg`,
    predmask2: `${baseUrl}/predmask2.jpg`
  }

  dialogVisible.value = true
}

const formatTime = (str) => {
  if (!str) return ''
  return new Date(str).toLocaleString()
}

onMounted(fetchData)
</script>

<style scoped>
.history-container { padding: 20px; }
.mini-img {
  width: 100%;
  height: 150px;
  background: #f0f0f0;
  border: 1px solid #ddd;
}
.row-group { margin-bottom: 15px; }
.group-title { margin: 5px 0; font-weight: bold; font-size: 14px; color: #555; }
.tag { font-size: 12px; color: #999; display: block; text-align: center; margin-bottom: 2px; }
</style>
