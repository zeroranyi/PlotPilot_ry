<template>
  <div class="refactor-panel">
    <header class="panel-header">
      <div class="header-main">
        <div class="title-row">
          <h3 class="panel-title">宏观诊断</h3>
          <n-tag size="small" round :bordered="false">Macro</n-tag>
        </div>
        <p class="panel-lead">
          Map-Reduce 式长文本理解入口：写仅在卷/部完成或人工触发时将提案写入 RefactorProposals；读在作者采纳后变为「补丁」，影响后续生成与对话中的自洽修补。
          <span class="panel-lead-accent">
            当前 Step1–2 为人设冲突断点 + 提案；全书剧情 Bug 扫描可在同一弹层内扩展为左侧列表、右侧修复稿形态。
          </span>
        </p>
      </div>
    </header>

    <n-alert
      v-if="macroDeskStale"
      type="info"
      :show-icon="true"
      closable
      style="margin: 0 16px 12px; font-size: 12px"
      @close="macroDeskStale = false"
    >
      检测到工作台已因<strong>新章节落库</strong>刷新：叙事事件与章节范围可能已变化。若需最新断点，请重新执行 Step1 扫描。
    </n-alert>

    <!-- 自动诊断结果展示 -->
    <div v-if="latestDiagnosis" class="step-block diagnosis-result-block">
      <div class="step-title">
        <n-tag :type="latestDiagnosis.resolved ? 'default' : (latestDiagnosis.status === 'completed' ? 'success' : 'error')" round size="small">
          {{ latestDiagnosis.resolved ? '已解决' : (latestDiagnosis.status === 'completed' ? '已完成' : '失败') }}
        </n-tag>
        <span>最近诊断结果</span>
        <n-text depth="3" style="font-size:12px">{{ formatTime(latestDiagnosis.created_at) }}</n-text>
        <n-button
          size="tiny"
          quaternary
          style="margin-left:auto"
          :loading="loadingDiagnosis"
          @click="loadLatestDiagnosis"
        >
          刷新
        </n-button>
      </div>

      <n-space vertical :size="8">
        <n-space align="center" :size="8">
          <n-text depth="3" style="font-size:12px">触发原因：</n-text>
          <n-tag size="small" round type="info">{{ latestDiagnosis.trigger_reason }}</n-tag>
          <n-text depth="3" style="font-size:12px">扫描人设：</n-text>
          <n-tag size="small" round>{{ latestDiagnosis.trait }}</n-tag>
        </n-space>

        <template v-if="latestDiagnosis.status === 'completed'">
          <!-- 已解决状态 -->
          <n-alert v-if="latestDiagnosis.resolved" type="success" :show-icon="true" style="font-size:12px">
            已标记为「已解决」，不再注入后续章节的提示词
            <template v-if="latestDiagnosis.resolved_at">
              <br>解决时间：{{ formatTime(latestDiagnosis.resolved_at) }}
            </template>
          </n-alert>
          <!-- 未解决且有断点 -->
          <template v-else-if="latestDiagnosis.breakpoint_count > 0">
            <n-alert type="warning" :show-icon="true" style="font-size:12px">
              发现 {{ latestDiagnosis.breakpoint_count }} 个冲突断点（会注入提示词）
              <n-button size="tiny" text type="primary" style="margin-left:8px" @click="useDiagnosisBreakpoints">
                查看详情
              </n-button>
            </n-alert>
            <n-button
              size="small"
              type="success"
              :loading="resolvingDiagnosis"
              @click="markAsResolved"
              style="margin-top:4px"
            >
              标记为已解决
            </n-button>
          </template>
          <!-- 未解决但无断点 -->
          <n-alert v-else type="success" :show-icon="true" style="font-size:12px">
            未发现冲突断点，人设一致性良好
          </n-alert>
        </template>

        <n-alert v-else type="error" :show-icon="true" style="font-size:12px">
          诊断失败：{{ latestDiagnosis.error_message || '未知错误' }}
        </n-alert>
      </n-space>
    </div>

    <!-- 快捷操作栏 -->
    <div class="step-block quick-actions">
      <n-space :size="10" align="center">
        <n-button
          type="primary"
          size="small"
          :loading="runningFullDiagnosis"
          @click="runFullDiagnosis"
        >
          <template #icon><span style="font-size:14px">🔍</span></template>
          全书诊断
        </n-button>
        <n-text depth="3" style="font-size:12px">
          扫描全部内置人设（冷酷、理性、谨慎、温和）
        </n-text>
      </n-space>
    </div>

    <!-- Step 1：扫描断点 -->
    <div class="step-block">
      <div class="step-title">
        <n-tag type="info" round size="small">Step 1</n-tag>
        <span>扫描人设冲突断点</span>
      </div>
      <n-space :size="10" align="flex-end" wrap>
        <n-form-item label="目标人设标签" label-placement="top" :show-feedback="false" style="flex:1;min-width:120px">
          <n-input v-model:value="scanTrait" placeholder="如：冷酷、理性、忠诚…" size="small" />
        </n-form-item>
        <n-form-item label="冲突标签（逗号分隔，可选）" label-placement="top" :show-feedback="false" style="flex:2;min-width:180px">
          <n-input v-model:value="scanConflictTags" placeholder="如：动机:冲动,情绪:崩溃" size="small" />
        </n-form-item>
        <n-button type="primary" size="small" :loading="scanning" @click="doScan">扫描</n-button>
      </n-space>

      <template v-if="breakpoints.length > 0">
        <n-divider style="margin:10px 0 6px" />
        <n-text depth="3" style="font-size:12px;margin-bottom:6px;display:block">
          找到 {{ breakpoints.length }} 个冲突断点，点击任意一个生成重构提案：
        </n-text>
        <n-space vertical :size="6">
          <n-card
            v-for="bp in breakpoints"
            :key="bp.event_id"
            size="small"
            hoverable
            :bordered="true"
            class="bp-card"
            :class="{ 'bp-card--active': selectedBreakpoint?.event_id === bp.event_id }"
            @click="selectBreakpoint(bp)"
          >
            <n-space align="center" justify="space-between">
              <n-space align="center" :size="8">
                <n-tag type="warning" size="tiny" round>第 {{ bp.chapter }} 章</n-tag>
                <n-text style="font-size:13px">{{ bp.reason }}</n-text>
              </n-space>
              <n-space :size="4" wrap>
                <n-tag v-for="t in bp.tags" :key="t" size="tiny" round type="error">{{ t }}</n-tag>
              </n-space>
            </n-space>
          </n-card>
        </n-space>
      </template>

      <n-empty v-else-if="scanned && breakpoints.length === 0" description="未发现冲突断点，人设一致性良好">
        <template #icon><span style="font-size:32px">✅</span></template>
      </n-empty>
    </div>

    <!-- Step 2：生成重构提案 -->
    <div v-if="selectedBreakpoint" class="step-block">
      <div class="step-title">
        <n-tag type="warning" round size="small">Step 2</n-tag>
        <span>生成重构提案</span>
        <n-text depth="3" style="font-size:12px">事件 {{ selectedBreakpoint.event_id }} · 第 {{ selectedBreakpoint.chapter }} 章</n-text>
      </div>

      <n-space vertical :size="10">
        <n-form-item label="当前事件摘要" label-placement="top" :show-feedback="false">
          <n-input
            v-model:value="proposalForm.current_event_summary"
            type="textarea"
            placeholder="当前章节发生了什么（从原文提取）"
            :autosize="{ minRows: 2, maxRows: 5 }"
            size="small"
          />
        </n-form-item>
        <n-form-item label="作者意图" label-placement="top" :show-feedback="false">
          <n-input
            v-model:value="proposalForm.author_intent"
            type="textarea"
            placeholder="你希望这个事件达到什么叙事目标？改动的核心是什么？"
            :autosize="{ minRows: 2, maxRows: 4 }"
            size="small"
          />
        </n-form-item>
        <n-button type="warning" size="small" :loading="proposalLoading" :disabled="!proposalForm.author_intent || !proposalForm.current_event_summary" @click="doGenerateProposal">
          生成重构提案
        </n-button>
      </n-space>

      <template v-if="proposal">
        <n-divider style="margin:10px 0 6px" />
        <n-space vertical :size="10">
          <div>
            <n-text strong style="font-size:13px;display:block;margin-bottom:6px">自然语言建议</n-text>
            <n-text style="font-size:13px;line-height:1.7">{{ proposal.natural_language_suggestion }}</n-text>
          </div>
          <div>
            <n-text strong style="font-size:13px;display:block;margin-bottom:6px">推理过程</n-text>
            <n-text depth="3" style="font-size:12px;line-height:1.6">{{ proposal.reasoning }}</n-text>
          </div>
          <div v-if="proposal.suggested_tags.length">
            <n-text strong style="font-size:13px;display:block;margin-bottom:6px">建议标签</n-text>
            <n-space :size="4" wrap>
              <n-tag v-for="t in proposal.suggested_tags" :key="t" size="small" round type="success">{{ t }}</n-tag>
            </n-space>
          </div>
          <div v-if="proposal.suggested_mutations.length">
            <n-text strong style="font-size:13px;display:block;margin-bottom:4px">
              建议的 Mutations（{{ proposal.suggested_mutations.length }} 个）
            </n-text>
            <n-code
              :code="JSON.stringify(proposal.suggested_mutations, null, 2)"
              language="json"
              word-wrap
              style="font-size:11px;max-height:160px;overflow:auto"
            />
          </div>
        </n-space>
      </template>
    </div>

    <!-- Step 3：应用修改 -->
    <div v-if="proposal && selectedBreakpoint" class="step-block">
      <div class="step-title">
        <n-tag type="success" round size="small">Step 3</n-tag>
        <span>应用修改</span>
      </div>

      <n-space vertical :size="10">
        <n-form-item label="修改原因（可选）" label-placement="top" :show-feedback="false">
          <n-input
            v-model:value="applyReason"
            placeholder="记录本次修改的决策原因（便于后续追溯）"
            size="small"
          />
        </n-form-item>

        <n-space :size="8">
          <n-button
            type="success"
            size="small"
            :loading="applyLoading"
            @click="doApply"
          >
            应用建议的全部 Mutations
          </n-button>
          <n-button secondary size="small" @click="resetAll">重新开始</n-button>
        </n-space>

        <template v-if="applyResult">
          <n-alert :type="applyResult.success ? 'success' : 'error'" :show-icon="true" style="font-size:13px">
            {{ applyResult.success
              ? `✓ 已成功应用 ${applyResult.applied_mutations.length} 个 Mutation`
              : '应用失败，请检查事件 ID 是否有效'
            }}
          </n-alert>
        </template>
      </n-space>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useWorkbenchRefreshStore } from '../../stores/workbenchRefreshStore'
import { useMessage } from 'naive-ui'
import { macroRefactorApi } from '../../api/tools'
import type { LogicBreakpoint, RefactorProposal, ApplyMutationResponse, MacroDiagnosisResult } from '../../api/tools'

interface Props { slug: string }
const props = defineProps<Props>()
const message = useMessage()

const macroDeskStale = ref(false)
const refreshStore = useWorkbenchRefreshStore()
const { deskTick } = storeToRefs(refreshStore)
watch(deskTick, () => {
  macroDeskStale.value = true
  loadLatestDiagnosis()
})

// 自动诊断结果
const latestDiagnosis = ref<MacroDiagnosisResult | null>(null)
const loadingDiagnosis = ref(false)
const runningFullDiagnosis = ref(false)
const resolvingDiagnosis = ref(false)

const loadLatestDiagnosis = async () => {
  loadingDiagnosis.value = true
  try {
    latestDiagnosis.value = await macroRefactorApi.getLatestDiagnosis(props.slug)
  } catch {
    // 静默失败
  } finally {
    loadingDiagnosis.value = false
  }
}

const runFullDiagnosis = async () => {
  runningFullDiagnosis.value = true
  try {
    const result = await macroRefactorApi.runDiagnosis(props.slug)
    latestDiagnosis.value = result
    if (result.status === 'completed') {
      if (result.breakpoint_count === 0) {
        message.success('诊断完成：未发现冲突断点')
      } else {
        message.warning(`诊断完成：发现 ${result.breakpoint_count} 个冲突断点`)
      }
    } else {
      message.error('诊断失败：' + (result.error_message || '未知错误'))
    }
  } catch {
    message.error('诊断请求失败')
  } finally {
    runningFullDiagnosis.value = false
  }
}

const markAsResolved = async () => {
  if (!latestDiagnosis.value) return
  
  resolvingDiagnosis.value = true
  try {
    const result = await macroRefactorApi.resolveDiagnosis(props.slug, latestDiagnosis.value.id)
    if (result.success) {
      // 更新本地状态
      latestDiagnosis.value = {
        ...latestDiagnosis.value,
        resolved: true,
        resolved_at: new Date().toISOString(),
        resolved_by: 'manual'
      }
      message.success(result.message)
    } else {
      message.error(result.message)
    }
  } catch {
    message.error('标记已解决失败')
  } finally {
    resolvingDiagnosis.value = false
  }
}

const useDiagnosisBreakpoints = () => {
  if (latestDiagnosis.value && latestDiagnosis.value.breakpoints.length > 0) {
    breakpoints.value = latestDiagnosis.value.breakpoints
    scanned.value = true
    scanTrait.value = latestDiagnosis.value.trait
    message.info(`已加载 ${breakpoints.value.length} 个诊断断点`)
  }
}

const formatTime = (iso: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

// Step 1 — 扫描
const scanTrait = ref('')
const scanConflictTags = ref('')
const scanning = ref(false)
const scanned = ref(false)
const breakpoints = ref<LogicBreakpoint[]>([])
const selectedBreakpoint = ref<LogicBreakpoint | null>(null)

const doScan = async () => {
  if (!scanTrait.value.trim()) { message.warning('请输入目标人设标签'); return }
  scanning.value = true
  scanned.value = false
  breakpoints.value = []
  selectedBreakpoint.value = null
  proposal.value = null
  applyResult.value = null
  try {
    breakpoints.value = await macroRefactorApi.scanBreakpoints(
      props.slug,
      scanTrait.value.trim(),
      scanConflictTags.value.trim() || undefined
    )
    scanned.value = true
    if (breakpoints.value.length === 0) message.success('未发现冲突断点')
    else message.warning(`发现 ${breakpoints.value.length} 个冲突断点`)
    macroDeskStale.value = false
  } catch {
    message.error('扫描失败')
  } finally {
    scanning.value = false
  }
}

const selectBreakpoint = (bp: LogicBreakpoint) => {
  selectedBreakpoint.value = bp
  proposal.value = null
  applyResult.value = null
  proposalForm.value = {
    current_event_summary: '',
    author_intent: '',
  }
}

// Step 2 — 生成提案
const proposalForm = ref({ current_event_summary: '', author_intent: '' })
const proposalLoading = ref(false)
const proposal = ref<RefactorProposal | null>(null)

const doGenerateProposal = async () => {
  if (!selectedBreakpoint.value) return
  proposalLoading.value = true
  try {
    proposal.value = await macroRefactorApi.generateProposal(props.slug, {
      event_id: selectedBreakpoint.value.event_id,
      author_intent: proposalForm.value.author_intent,
      current_event_summary: proposalForm.value.current_event_summary,
      current_tags: selectedBreakpoint.value.tags,
    })
  } catch {
    message.error('生成提案失败')
  } finally {
    proposalLoading.value = false
  }
}

// Step 3 — 应用
const applyReason = ref('')
const applyLoading = ref(false)
const applyResult = ref<ApplyMutationResponse | null>(null)

const doApply = async () => {
  if (!selectedBreakpoint.value || !proposal.value) return
  applyLoading.value = true
  try {
    applyResult.value = await macroRefactorApi.applyMutations(props.slug, {
      event_id: selectedBreakpoint.value.event_id,
      mutations: proposal.value.suggested_mutations,
      reason: applyReason.value || undefined,
    })
    if (applyResult.value.success) message.success('Mutations 已成功应用')
    else message.error('应用失败')
  } catch {
    message.error('应用失败，请检查事件数据')
  } finally {
    applyLoading.value = false
  }
}

const resetAll = () => {
  selectedBreakpoint.value = null
  proposal.value = null
  applyResult.value = null
  applyReason.value = ''
}

// 初始化
onMounted(() => {
  loadLatestDiagnosis()
})
</script>

<style scoped>
.refactor-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  background: linear-gradient(to bottom, var(--n-color-modal) 0%, rgba(245, 158, 11, 0.02) 100%);
  gap: 0;
}

.panel-header {
  padding: 16px 20px 14px;
  border-bottom: 1px solid var(--aitext-split-border);
  background: var(--app-surface);
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.panel-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.panel-lead {
  margin: 0;
  font-size: 12px;
  line-height: 1.65;
  color: var(--text-color-3);
}

.panel-lead-accent {
  display: block;
  margin-top: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  border-left: 3px solid rgba(245, 158, 11, 0.85);
  background: rgba(245, 158, 11, 0.07);
  color: #b45309;
  font-weight: 500;
  line-height: 1.55;
}

.step-block {
  padding: 18px 20px;
  border-bottom: 1px solid var(--aitext-split-border);
  background: var(--app-surface);
  flex-shrink: 0;
  transition: background 0.2s ease;
}

.step-block:hover {
  background: rgba(245, 158, 11, 0.02);
}

.step-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 14px;
  color: var(--text-color-1);
  letter-spacing: 0.01em;
}

.diagnosis-result-block {
  background: linear-gradient(to right, rgba(34, 197, 94, 0.03), rgba(59, 130, 246, 0.02));
}

.quick-actions {
  background: rgba(99, 102, 241, 0.02);
}

.bp-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border-radius: 10px;
  overflow: hidden;
}

.bp-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.bp-card--active {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2), 0 4px 16px rgba(79, 70, 229, 0.15);
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.05), rgba(99, 102, 241, 0.08));
}

.refactor-panel :deep(.n-alert) {
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.refactor-panel :deep(.n-card) {
  border-radius: 10px;
  transition: all 0.2s ease;
}

.refactor-panel :deep(.n-form-item) {
  margin-bottom: 0;
}

.refactor-panel :deep(.n-input),
.refactor-panel :deep(.n-input-number) {
  border-radius: 8px;
}

.refactor-panel :deep(.n-button) {
  border-radius: 8px;
  font-weight: 500;
}

.refactor-panel :deep(.n-divider) {
  margin: 12px 0;
}

.refactor-panel :deep(.n-code) {
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.03);
}
</style>
