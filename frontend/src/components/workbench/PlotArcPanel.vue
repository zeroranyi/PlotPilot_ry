<template>
  <div class="plot-arc-panel">
    <header class="panel-header">
      <div class="header-main">
        <div class="title-row">
          <h3 class="panel-title">情节弧线设计</h3>
          <n-tag size="small" round :bordered="false">Plot Arc</n-tag>
        </div>
        <p class="panel-lead">
          设计小说的<strong>情节张力曲线</strong>，规划起承转合的关键剧情点和节奏控制。
        </p>
      </div>
      <n-space class="header-actions" :size="8" align="center" :wrap="false">
        <n-button class="panel-header-btn" size="small" type="primary" secondary @click="showAddPointModal = true">
          + 添加剧情点
        </n-button>
        <n-button class="panel-header-btn" size="small" type="primary" :loading="saving" @click="savePlotArc">
          保存弧线
        </n-button>
      </n-space>
    </header>

    <div class="panel-content">
      <n-spin :show="loading">
        <n-empty
          v-if="plotPoints.length === 0"
          class="panel-empty"
          size="small"
          description="暂无剧情点"
        >
          <template #icon>
            <span class="panel-empty-ico" aria-hidden="true">📈</span>
          </template>
          <template #extra>
            <n-text depth="3" style="font-size: 12px; text-align: center; max-width: 280px">
              点击「添加剧情点」标记开端/高潮等关键节点，保存后上方概览卡会显示张力曲线。
            </n-text>
          </template>
        </n-empty>

        <div v-else class="plot-arc-container">
          <!-- 张力曲线可视化 -->
          <div class="tension-chart">
            <n-card size="small" title="张力曲线预览" :bordered="true">
              <div class="chart-wrapper">
                <svg viewBox="0 0 800 200" class="tension-svg">
                  <!-- 网格线 -->
                  <line v-for="i in 4" :key="`grid-${i}`"
                    :x1="0" :y1="i * 50" :x2="800" :y2="i * 50"
                    stroke="#e0e0e0" stroke-width="1" stroke-dasharray="4,4" />

                  <!-- 张力曲线 -->
                  <polyline
                    :points="tensionCurvePoints"
                    fill="none"
                    stroke="#18a058"
                    stroke-width="3"
                  />

                  <!-- 剧情点标记 -->
                  <g v-for="(point, index) in sortedPlotPoints" :key="point.chapter_number">
                    <circle
                      :cx="getChapterX(point.chapter_number)"
                      :cy="getTensionY(point.tension)"
                      r="6"
                      :fill="getPointColor(point.point_type)"
                      stroke="white"
                      stroke-width="2"
                    />
                    <text
                      :x="getChapterX(point.chapter_number)"
                      :y="getTensionY(point.tension) - 15"
                      text-anchor="middle"
                      font-size="12"
                      fill="#666"
                    >
                      Ch{{ point.chapter_number }}
                    </text>
                  </g>
                </svg>
              </div>
            </n-card>
          </div>

          <!-- 剧情点列表 -->
          <n-space vertical :size="12" class="plot-points-list">
            <n-card
              v-for="(point, index) in sortedPlotPoints"
              :key="index"
              size="small"
              :bordered="true"
              hoverable
            >
              <template #header>
                <div class="point-header">
                  <div class="point-header-main">
                    <n-tag :type="getPointTypeColor(point.point_type)" size="small" round>
                      {{ getPointTypeLabel(point.point_type) }}
                    </n-tag>
                    <n-text class="point-title" strong>第 {{ point.chapter_number }} 章</n-text>
                    <n-tag :type="getTensionTypeColor(point.tension)" size="small" round>
                      张力 {{ getTensionLabel(point.tension) }}
                    </n-tag>
                  </div>
                  <n-space :size="6" class="point-header-actions" @click.stop>
                    <n-button size="tiny" secondary @click="editPoint(index)">编辑</n-button>
                    <n-button size="tiny" type="error" secondary @click="deletePoint(index)">删除</n-button>
                  </n-space>
                </div>
              </template>

              <n-text style="font-size: 13px; line-height: 1.55">{{ point.description }}</n-text>
            </n-card>
          </n-space>
        </div>
      </n-spin>
    </div>

    <!-- 添加/编辑剧情点模态框 -->
    <n-modal v-model:show="showAddPointModal" preset="card" title="添加剧情点" style="width: 600px">
      <n-form ref="formRef" :model="formData" :rules="formRules" label-placement="left" label-width="100">
        <n-form-item label="章节号" path="chapter_number">
          <n-input-number
            v-model:value="formData.chapter_number"
            :min="1"
            placeholder="剧情点所在章节"
            style="width: 100%"
          />
        </n-form-item>

        <n-form-item label="剧情点类型" path="point_type">
          <n-select
            v-model:value="formData.point_type"
            :options="pointTypeOptions"
            placeholder="选择剧情点类型"
          />
        </n-form-item>

        <n-form-item label="张力等级" path="tension">
          <n-select
            v-model:value="formData.tension"
            :options="tensionOptions"
            placeholder="选择张力等级"
          />
        </n-form-item>

        <n-form-item label="描述" path="description">
          <n-input
            v-model:value="formData.description"
            type="textarea"
            placeholder="描述这个剧情点的内容和作用"
            :rows="4"
          />
        </n-form-item>
      </n-form>

      <template #action>
        <n-space justify="end">
          <n-button @click="showAddPointModal = false">取消</n-button>
          <n-button type="primary" @click="handleAddPoint">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useMessage } from 'naive-ui'
import { workflowApi } from '../../api/workflow'
import type { PlotPointDTO } from '../../api/workflow'

interface Props {
  slug: string
}

const props = defineProps<Props>()
const message = useMessage()

const loading = ref(false)
const saving = ref(false)
const plotPoints = ref<PlotPointDTO[]>([])
const showAddPointModal = ref(false)
const editingIndex = ref(-1)

const formData = ref({
  chapter_number: 1,
  point_type: 'opening',
  tension: 1,
  description: ''
})

const formRules = {
  chapter_number: { required: true, type: 'number', message: '请输入章节号', trigger: 'blur' },
  point_type: { required: true, message: '请选择剧情点类型', trigger: 'change' },
  tension: { required: true, type: 'number', message: '请选择张力等级', trigger: 'change' },
  description: { required: true, message: '请输入描述', trigger: 'blur' }
}

const pointTypeOptions = [
  { label: '开端', value: 'opening' },
  { label: '上升', value: 'rising' },
  { label: '转折', value: 'turning' },
  { label: '高潮', value: 'climax' },
  { label: '下降', value: 'falling' },
  { label: '结局', value: 'resolution' }
]

const tensionOptions = [
  { label: '平缓 (1)', value: 1 },
  { label: '中等 (2)', value: 2 },
  { label: '紧张 (3)', value: 3 },
  { label: '极度紧张 (4)', value: 4 }
]

const sortedPlotPoints = computed(() => {
  return [...plotPoints.value].sort((a, b) => a.chapter_number - b.chapter_number)
})

const maxChapter = computed(() => {
  if (plotPoints.value.length === 0) return 100
  return Math.max(...plotPoints.value.map(p => p.chapter_number), 100)
})

const tensionCurvePoints = computed(() => {
  if (sortedPlotPoints.value.length === 0) return ''

  return sortedPlotPoints.value
    .map(point => `${getChapterX(point.chapter_number)},${getTensionY(point.tension)}`)
    .join(' ')
})

const getChapterX = (chapter: number) => {
  return (chapter / maxChapter.value) * 750 + 25
}

const getTensionY = (tension: number) => {
  return 180 - ((tension - 1) / 3) * 150
}

const getPointColor = (pointType: string) => {
  const colors: Record<string, string> = {
    opening: '#2080f0',
    rising: '#18a058',
    turning: '#f0a020',
    climax: '#d03050',
    falling: '#9c27b0',
    resolution: '#0e7a0d'
  }
  return colors[pointType] || '#666'
}

const getPointTypeLabel = (type: string) => {
  const option = pointTypeOptions.find(o => o.value === type)
  return option?.label || type
}

const getPointTypeColor = (type: string) => {
  const colors: Record<string, any> = {
    opening: 'info',
    rising: 'success',
    turning: 'warning',
    climax: 'error',
    falling: 'default',
    resolution: 'success'
  }
  return colors[type] || 'default'
}

const getTensionLabel = (tension: number) => {
  const labels: Record<number, string> = {
    1: '平缓',
    2: '中等',
    3: '紧张',
    4: '极度紧张'
  }
  return labels[tension] || tension.toString()
}

const getTensionTypeColor = (tension: number) => {
  if (tension >= 4) return 'error'
  if (tension >= 3) return 'warning'
  if (tension >= 2) return 'info'
  return 'default'
}

const loadPlotArc = async () => {
  loading.value = true
  try {
    const arc = await workflowApi.getPlotArc(props.slug)
    plotPoints.value = arc.key_points || []
  } catch (error: any) {
    if (error?.status === 404 || error?.response?.status === 404) {
      plotPoints.value = []
    } else {
      message.error(error?.detail || '加载情节弧线失败')
    }
  } finally {
    loading.value = false
  }
}

const handleAddPoint = () => {
  if (editingIndex.value >= 0) {
    plotPoints.value[editingIndex.value] = { ...formData.value }
    editingIndex.value = -1
  } else {
    plotPoints.value.push({ ...formData.value })
  }

  showAddPointModal.value = false
  formData.value = {
    chapter_number: 1,
    point_type: 'opening',
    tension: 1,
    description: ''
  }
}

const editPoint = (index: number) => {
  editingIndex.value = index
  formData.value = { ...sortedPlotPoints.value[index] }
  showAddPointModal.value = true
}

const deletePoint = (index: number) => {
  const point = sortedPlotPoints.value[index]
  const originalIndex = plotPoints.value.findIndex(
    p => p.chapter_number === point.chapter_number && p.description === point.description
  )
  if (originalIndex >= 0) {
    plotPoints.value.splice(originalIndex, 1)
  }
}

const savePlotArc = async () => {
  if (plotPoints.value.length === 0) {
    message.warning('请至少添加一个剧情点')
    return
  }

  saving.value = true
  try {
    await workflowApi.createPlotArc(props.slug, { key_points: plotPoints.value })
    message.success('情节弧线保存成功')
  } catch (error: any) {
    message.error(error?.detail || '保存情节弧线失败')
  } finally {
    saving.value = false
  }
}

watch(() => props.slug, (slug) => {
  if (slug) loadPlotArc()
})

onMounted(() => {
  loadPlotArc()
})
</script>

<style scoped>
.plot-arc-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--aitext-panel-muted);
}

.panel-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--aitext-split-border);
  background: var(--app-surface);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.header-main {
  flex: 1;
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.panel-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color-1);
}

.panel-lead {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-color-3);
}

.header-actions {
  flex-shrink: 0;
  align-items: center;
}

.panel-header-btn {
  height: 28px !important;
  min-height: 28px !important;
  padding: 0 12px !important;
}

.panel-empty {
  padding: 12px 8px !important;
  min-height: auto !important;
}

.panel-empty-ico {
  font-size: 36px;
  line-height: 1;
  opacity: 0.9;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px;
}

.plot-arc-panel :deep(.tension-chart .n-card) {
  overflow: visible;
}

.plot-arc-panel :deep(.tension-chart .n-card__content) {
  padding: 8px 12px !important;
}

.plot-arc-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tension-chart {
  width: 100%;
}

.chart-wrapper {
  width: 100%;
  height: 220px;
  overflow: hidden;
}

.tension-svg {
  width: 100%;
  height: 100%;
}

.plot-points-list {
  width: 100%;
}

.point-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  width: 100%;
  flex-wrap: wrap;
}

.point-header-main {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  min-width: 0;
}

.point-title {
  font-size: 14px;
  margin: 0;
}

.point-header-actions {
  flex-shrink: 0;
}
</style>
