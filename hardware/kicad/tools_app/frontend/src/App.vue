<template>
  <div class="shell">
    <header>
      <div>
        <span class="eyebrow">LOCAL WORKBENCH</span>
        <h1>KiCad Tools</h1>
      </div>
      <div class="health">
        <span :class="['dot', health?.pcb_editor_reachable ? 'ready' : '']"></span
        >{{ health?.pcb_editor_reachable ? 'PCB Editor ready' : 'PCB Editor offline' }}
      </div>
    </header>
    <nav aria-label="Main navigation">
      <button
        v-for="item in tabs"
        :key="item"
        :class="{ active: tab === item }"
        @click="tab = item"
      >
        {{ item }}
      </button>
    </nav>
    <main>
      <p v-if="error" class="message error" role="alert">{{ error }}</p>
      <p v-if="notice" class="message">{{ notice }}</p>
      <section v-if="tab === 'Modules'" class="catalogue">
        <aside>
          <h2>Tool catalogue</h2>
          <p class="muted">Choose an approved tool. Inputs are validated again by the backend.</p>
          <div v-for="group in groupedModules" :key="group.category" class="group">
            <h3>{{ title(group.category) }}</h3>
            <button
              v-for="module in group.items"
              :key="module.id"
              :class="['module-button', { selected: selected?.id === module.id }]"
              @click="selectModule(module)"
            >
              <span
                >{{ module.name }}<small>{{ module.execution_type.replace('_', ' ') }}</small></span
              >
            </button>
          </div>
        </aside>
        <article v-if="selected" class="panel">
          <div class="panel-heading">
            <div>
              <span :class="['badge', selected.risk.level]">{{ selected.risk.level }} risk</span>
              <h2>{{ selected.name }}</h2>
            </div>
            <span class="timeout">Timeout {{ selected.timeout_seconds }}s</span>
          </div>
          <p>{{ selected.description }}</p>
          <form @submit.prevent="submitRun">
            <div v-for="parameter in selected.parameters" :key="parameter.name" class="field">
              <label :for="parameter.name"
                >{{ parameter.label }} <span v-if="parameter.required">*</span></label
              >
              <p>{{ parameter.description }}</p>
              <input
                v-if="['string', 'file', 'directory'].includes(parameter.type)"
                :id="parameter.name"
                v-model="form[parameter.name]"
                type="text"
                :required="parameter.required"
                :placeholder="parameter.extensions?.join(', ')"
              />
              <input
                v-else-if="parameter.type === 'integer' || parameter.type === 'number'"
                :id="parameter.name"
                v-model.number="form[parameter.name]"
                type="number"
                :step="parameter.type === 'integer' ? 1 : 'any'"
                :min="parameter.minimum"
                :max="parameter.maximum"
                :required="parameter.required"
              />
              <select
                v-else-if="parameter.type === 'enum'"
                :id="parameter.name"
                v-model="form[parameter.name]"
                :required="parameter.required"
              >
                <option v-for="choice in parameter.choices" :key="String(choice)" :value="choice">
                  {{ choice }}
                </option>
              </select>
              <label v-else-if="parameter.type === 'boolean'" class="checkbox"
                ><input :id="parameter.name" v-model="form[parameter.name]" type="checkbox" />
                Enabled</label
              ><textarea
                v-else
                :id="parameter.name"
                v-model="listForm[parameter.name]"
                rows="3"
                placeholder="One value per line"
              ></textarea>
            </div>
            <div v-if="selected.risk.confirmation_required" class="confirm">
              <strong>Confirmation required</strong>
              <p>{{ selected.risk.summary }}</p>
              <label class="checkbox"
                ><input v-model="confirmed" type="checkbox" /> I understand and want to run this
                tool.</label
              >
            </div>
            <button
              class="primary"
              type="submit"
              :disabled="submitting || (selected.risk.confirmation_required && !confirmed)"
            >
              {{ submitting ? 'Submitting…' : 'Run tool' }}
            </button>
          </form>
        </article>
        <article v-else class="panel empty">
          <h2>Select a tool</h2>
          <p>Its metadata-generated form will appear here.</p>
        </article>
      </section>
      <section v-else-if="tab === 'Runs'" class="runs-layout">
        <div class="panel history">
          <div class="panel-heading">
            <h2>Run history</h2>
            <button @click="loadRuns">Refresh</button>
          </div>
          <button
            v-for="run in runs"
            :key="run.id"
            :class="['run-row', { selected: activeRun?.id === run.id }]"
            @click="showRun(run)"
          >
            <span
              ><strong>{{ moduleName(run.module_id) }}</strong
              ><small>{{ formatDate(run.created_at) }}</small></span
            ><span :class="['status', run.status]">{{ run.status }}</span>
          </button>
          <p v-if="runs.length === 0" class="muted">No runs yet.</p>
        </div>
        <article class="panel output">
          <template v-if="activeRun"
            ><div class="panel-heading">
              <div>
                <h2>{{ moduleName(activeRun.module_id) }}</h2>
                <code>{{ activeRun.id }}</code>
              </div>
              <button v-if="isActive(activeRun)" @click="cancelRun">Cancel</button>
            </div>
            <p>
              <span :class="['status', activeRun.status]">{{ activeRun.status }}</span
              ><span v-if="activeRun.exit_code !== null"> Exit code {{ activeRun.exit_code }}</span>
            </p>
            <p v-if="activeRun.error_summary" class="message error">
              {{ activeRun.error_summary }}
            </p>
            <h3>Standard output</h3>
            <pre>{{ output.stdout || 'No output.' }}</pre>
            <h3>Standard error</h3>
            <pre class="stderr">{{ output.stderr || 'No errors.' }}</pre></template
          ><template v-else
            ><h2>Run details</h2>
            <p class="muted">Select a run to inspect its state and logs.</p></template
          >
        </article>
      </section>
      <section v-else-if="tab === 'Readiness'" class="panel readiness">
        <h2>Application readiness</h2>
        <div v-if="health" class="checks">
          <div v-for="check in readinessChecks" :key="check.label">
            <span :class="['check', check.ok ? 'ok' : '']">{{ check.ok ? '✓' : '×' }}</span
            ><span
              ><strong>{{ check.label }}</strong
              ><small>{{ check.detail }}</small></span
            >
          </div>
        </div>
      </section>
      <section v-else class="panel settings">
        <h2>Settings</h2>
        <p class="muted">Changes affect new runs. Paths must exist on the backend host.</p>
        <form v-if="settings" @submit.prevent="saveSettings">
          <label>Allowed project roots<textarea v-model="rootsText" rows="4"></textarea></label
          ><label>Python executable<input v-model="settings.python_executable" required /></label
          ><label>KiCad executable<input v-model="settings.kicad_executable" required /></label
          ><label
            >KiCad CLI executable<input v-model="settings.kicad_cli_executable" required
          /></label>
          <div class="columns">
            <label
              >Maximum concurrent runs<input
                v-model.number="settings.max_concurrent_runs"
                type="number"
                min="1"
                max="16" /></label
            ><label
              >History limit<input
                v-model.number="settings.history_limit"
                type="number"
                min="1"
                max="10000"
            /></label>
          </div>
          <button class="primary" type="submit">Save settings</button>
        </form>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue';
import {
  api,
  type AppSettings,
  type HealthReport,
  type ModuleDefinition,
  type RunOutput,
  type RunRecord
} from '@/api';
const tabs = ['Modules', 'Runs', 'Readiness', 'Settings'] as const;
const tab = ref<(typeof tabs)[number]>('Modules');
const modules = ref<ModuleDefinition[]>([]);
const runs = ref<RunRecord[]>([]);
const selected = ref<ModuleDefinition>();
const activeRun = ref<RunRecord>();
const output = ref<RunOutput>({ stdout: '', stderr: '' });
const health = ref<HealthReport>();
const settings = ref<AppSettings>();
const form = ref<Record<string, unknown>>({});
const listForm = ref<Record<string, string>>({});
const confirmed = ref(false);
const submitting = ref(false);
const error = ref('');
const notice = ref('');
const rootsText = ref('');
let pollTimer: ReturnType<typeof setTimeout> | undefined;
const groupedModules = computed(() =>
  [...new Set(modules.value.map((item) => item.category))].map((category) => ({
    category,
    items: modules.value.filter((item) => item.category === category)
  }))
);
const readinessChecks = computed(() =>
  health.value
    ? [
        {
          label: 'Python',
          ok: health.value.python.available,
          detail: health.value.python.resolved ?? health.value.python.configured
        },
        {
          label: 'KiCad',
          ok: health.value.kicad.available,
          detail: health.value.kicad.resolved ?? 'Not found'
        },
        {
          label: 'KiCad CLI',
          ok: health.value.kicad_cli.available,
          detail: health.value.kicad_cli.resolved ?? 'Not found'
        },
        {
          label: 'kipy package',
          ok: health.value.kipy_importable,
          detail: health.value.kipy_importable ? 'Importable' : 'Not importable'
        },
        {
          label: 'PCB Editor API',
          ok: health.value.pcb_editor_reachable,
          detail: health.value.kicad_api_socket ?? 'No API socket found'
        }
      ]
    : []
);
const title = (value: string): string =>
  value.replace(/-/g, ' ').replace(/^./, (letter: string) => letter.toUpperCase());
const formatDate = (value: string): string =>
  new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(
    new Date(value)
  );
const moduleName = (id: string): string => modules.value.find((item) => item.id === id)?.name ?? id;
const isActive = (run: RunRecord): boolean => run.status === 'queued' || run.status === 'running';
const report = (caught: unknown): void => {
  error.value = caught instanceof Error ? caught.message : 'Unexpected error';
};
const clearMessages = (): void => {
  error.value = '';
  notice.value = '';
};
const selectModule = (module: ModuleDefinition): void => {
  selected.value = module;
  confirmed.value = false;
  form.value = {};
  listForm.value = {};
  for (const parameter of module.parameters) {
    if (parameter.type === 'string_list')
      listForm.value[parameter.name] = Array.isArray(parameter.default)
        ? parameter.default.join('\n')
        : '';
    else
      form.value[parameter.name] = parameter.default ?? (parameter.type === 'boolean' ? false : '');
  }
};
const parameters = (): Record<string, unknown> => {
  const values: Record<string, unknown> = {};
  if (!selected.value) return values;
  for (const parameter of selected.value.parameters) {
    const value =
      parameter.type === 'string_list'
        ? (listForm.value[parameter.name] ?? '')
            .split('\n')
            .map((item) => item.trim())
            .filter(Boolean)
        : form.value[parameter.name];
    if (value !== '' && value !== null && value !== undefined) values[parameter.name] = value;
  }
  return values;
};
const submitRun = async (): Promise<void> => {
  if (!selected.value) return;
  clearMessages();
  submitting.value = true;
  try {
    const run = await api.start(selected.value.id, parameters(), confirmed.value);
    await loadRuns();
    await showRun(run);
    tab.value = 'Runs';
  } catch (caught) {
    report(caught);
  } finally {
    submitting.value = false;
  }
};
const loadRuns = async (): Promise<void> => {
  try {
    runs.value = await api.runs();
  } catch (caught) {
    report(caught);
  }
};
const showRun = async (run: RunRecord): Promise<void> => {
  if (pollTimer) clearTimeout(pollTimer);
  try {
    activeRun.value = await api.run(run.id);
    output.value = await api.output(run.id);
    if (isActive(activeRun.value))
      pollTimer = setTimeout(() => void showRun(activeRun.value as RunRecord), 1000);
  } catch (caught) {
    report(caught);
  }
};
const cancelRun = async (): Promise<void> => {
  if (!activeRun.value) return;
  try {
    activeRun.value = await api.cancel(activeRun.value.id);
    await showRun(activeRun.value);
    await loadRuns();
  } catch (caught) {
    report(caught);
  }
};
const saveSettings = async (): Promise<void> => {
  if (!settings.value) return;
  clearMessages();
  try {
    settings.value.allowed_roots = rootsText.value
      .split('\n')
      .map((item) => item.trim())
      .filter(Boolean);
    settings.value = await api.saveSettings(settings.value);
    rootsText.value = settings.value.allowed_roots.join('\n');
    notice.value = 'Settings saved.';
  } catch (caught) {
    report(caught);
  }
};
onMounted(async () => {
  try {
    const [moduleData, runData, healthData, settingsData] = await Promise.all([
      api.modules(),
      api.runs(),
      api.health(),
      api.settings()
    ]);
    modules.value = moduleData;
    runs.value = runData;
    health.value = healthData;
    settings.value = settingsData;
    rootsText.value = settingsData.allowed_roots.join('\n');
    if (moduleData[0]) selectModule(moduleData[0]);
  } catch (caught) {
    report(caught);
  }
});
onBeforeUnmount(() => {
  if (pollTimer) clearTimeout(pollTimer);
});
</script>

<style scoped>
:global(*) {
  box-sizing: border-box;
}
:global(body) {
  margin: 0;
  background: #f3f1eb;
  color: #20241f;
  font-family: Inter, ui-sans-serif, system-ui, sans-serif;
}
.shell {
  max-width: 1380px;
  margin: auto;
  min-height: 100vh;
  padding: 28px 36px;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #c9c9bf;
  padding-bottom: 20px;
}
h1,
h2,
h3,
p {
  margin-top: 0;
}
h1 {
  font-size: 2rem;
  margin: 3px 0 0;
  letter-spacing: -0.04em;
}
.eyebrow {
  font: 700 0.68rem ui-monospace;
  letter-spacing: 0.18em;
  color: #4b6758;
}
.health {
  font-size: 0.85rem;
}
.dot {
  display: inline-block;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: #a54d3c;
  margin-right: 8px;
}
.dot.ready {
  background: #3b7957;
}
nav {
  display: flex;
  gap: 5px;
  padding: 18px 0;
}
button {
  font: inherit;
  cursor: pointer;
  border: 1px solid #c5c5ba;
  background: #f9f8f3;
  padding: 9px 13px;
  border-radius: 5px;
  color: inherit;
}
nav button {
  border-color: transparent;
  background: transparent;
}
nav button.active {
  background: #263a30;
  color: #fff;
}
.catalogue,
.runs-layout {
  display: grid;
  grid-template-columns: 310px 1fr;
  gap: 20px;
}
aside {
  padding-right: 10px;
}
.muted,
.field p,
small {
  color: #69716b;
}
.group h3 {
  font: 700 0.68rem ui-monospace;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin: 22px 0 8px;
}
.module-button,
.run-row {
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: center;
  text-align: left;
  margin-bottom: 6px;
}
.module-button span,
.run-row strong {
  display: block;
}
.module-button small,
.run-row small {
  display: block;
  margin-top: 4px;
}
.selected {
  border-color: #486452;
  background: #e5ebe3;
}
.panel {
  background: #fff;
  border: 1px solid #d5d4ca;
  border-radius: 8px;
  padding: 26px;
  box-shadow: 0 2px 10px #2432280a;
}
.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 20px;
}
.panel-heading h2 {
  margin: 7px 0;
}
.badge,
.status {
  display: inline-block;
  border-radius: 100px;
  padding: 4px 8px;
  font: 700 0.66rem ui-monospace;
  text-transform: uppercase;
  background: #e7e8e3;
}
.badge.medium,
.badge.high,
.status.failed,
.status.timed_out {
  background: #f3dfc9;
  color: #7b3f22;
}
.badge.low,
.status.succeeded {
  background: #dceadf;
  color: #28603d;
}
.status.running,
.status.queued {
  background: #dbe7ed;
  color: #28566b;
}
.timeout {
  color: #69716b;
  font-size: 0.8rem;
}
.field {
  margin: 22px 0;
}
.field > label,
.settings label {
  display: block;
  font-weight: 650;
}
.field p {
  font-size: 0.82rem;
  margin: 5px 0 8px;
}
input,
select,
textarea {
  display: block;
  width: 100%;
  margin-top: 7px;
  border: 1px solid #bdbfb5;
  border-radius: 4px;
  padding: 10px;
  background: #fbfbf8;
  font: inherit;
}
.checkbox {
  display: flex !important;
  align-items: center;
  gap: 8px;
  font-weight: 400 !important;
}
.checkbox input {
  display: inline;
  width: auto;
  margin: 0;
}
.confirm {
  background: #fff4dc;
  border-left: 3px solid #b07723;
  padding: 14px;
  margin: 22px 0;
}
.confirm p {
  margin: 6px 0 12px;
}
.primary {
  background: #263a30;
  color: white;
  border-color: #263a30;
  padding: 11px 18px;
}
.primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.message {
  padding: 12px 15px;
  background: #e5ebe3;
  border-radius: 5px;
}
.message.error {
  background: #f5dfda;
  color: #7a2f24;
}
.empty {
  text-align: center;
  padding-top: 100px;
}
.history {
  padding: 18px;
}
.run-row {
  border: 0;
  border-bottom: 1px solid #e2e2da;
  border-radius: 0;
  background: transparent;
}
.output pre {
  background: #18201b;
  color: #dfe7e1;
  min-height: 100px;
  max-height: 330px;
  overflow: auto;
  padding: 15px;
  border-radius: 5px;
  white-space: pre-wrap;
}
.output pre.stderr {
  color: #f3c8be;
}
.output code {
  font-size: 0.7rem;
  color: #69716b;
}
.checks {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}
.checks > div {
  display: flex;
  align-items: center;
  gap: 12px;
  border: 1px solid #e0dfd6;
  padding: 14px;
}
.checks small {
  display: block;
  margin-top: 3px;
  word-break: break-all;
}
.check {
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #f2dcd7;
  color: #8a3026;
}
.check.ok {
  background: #dceadf;
  color: #28603d;
}
.settings form {
  max-width: 750px;
}
.settings label {
  margin: 18px 0;
}
.columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
@media (max-width: 760px) {
  .shell {
    padding: 20px 15px;
  }
  .catalogue,
  .runs-layout {
    grid-template-columns: 1fr;
  }
  header {
    align-items: flex-start;
  }
  .health {
    margin-top: 8px;
  }
  .columns {
    grid-template-columns: 1fr;
  }
  nav {
    overflow: auto;
  }
}
</style>
