import { flushPromises, mount } from '@vue/test-utils';
import { afterEach, describe, expect, it, vi } from 'vitest';
import App from '@/App.vue';

const moduleDefinition = {
  id: 'panelize',
  name: 'Panelize PCB',
  description: 'Build a panel.',
  category: 'manufacturing',
  execution_type: 'file_generate',
  requires_kicad: false,
  requires_pcb_editor: false,
  requires_kicad_api: false,
  timeout_seconds: 60,
  parameters: [
    {
      name: 'input',
      label: 'Input PCB',
      description: 'Board path.',
      kind: 'positional',
      type: 'file',
      required: true,
      default: null,
      extensions: ['.kicad_pcb']
    },
    {
      name: 'count',
      label: 'Count',
      description: 'Board count.',
      kind: 'option',
      type: 'integer',
      required: true,
      default: 2,
      minimum: 1
    }
  ],
  risk: { level: 'medium', summary: 'Writes a file.', confirmation_required: true }
};
const settings = {
  allowed_roots: ['/projects'],
  python_executable: '/python',
  kicad_executable: 'kicad',
  kicad_cli_executable: 'kicad-cli',
  max_concurrent_runs: 2,
  history_limit: 200,
  frontend_origin: 'http://localhost:5173'
};
const health = {
  status: 'ok',
  python: { configured: '/python', available: true, resolved: '/python' },
  kicad: { configured: 'kicad', available: false, resolved: null },
  kicad_cli: { configured: 'kicad-cli', available: true, resolved: '/kicad-cli' },
  kipy_importable: true,
  kicad_api_socket: null,
  pcb_editor_reachable: false
};

const mockFetch = (extra?: (url: string, init?: RequestInit) => Response | undefined): void => {
  vi.stubGlobal(
    'fetch',
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      const custom = extra?.(url, init);
      if (custom) return Promise.resolve(custom);
      const data =
        url === '/api/modules'
          ? [moduleDefinition]
          : url === '/api/runs'
            ? []
            : url === '/api/health'
              ? health
              : settings;
      return Promise.resolve(
        new Response(JSON.stringify(data), {
          status: 200,
          headers: { 'Content-Type': 'application/json' }
        })
      );
    })
  );
};

afterEach(() => vi.unstubAllGlobals());

describe('App', () => {
  it('builds module forms from API metadata and requires risk confirmation', async () => {
    mockFetch();
    const wrapper = mount(App);
    await flushPromises();
    expect(wrapper.text()).toContain('Panelize PCB');
    expect(wrapper.find('input#input').exists()).toBe(true);
    expect(wrapper.find('input#count').attributes('min')).toBe('1');
    const runButton = wrapper.get('button[type="submit"]');
    expect(runButton.attributes('disabled')).toBeDefined();
    await wrapper.get('.confirm input').setValue(true);
    expect(runButton.attributes('disabled')).toBeUndefined();
  });

  it('shows backend validation errors clearly', async () => {
    mockFetch((url, init) =>
      url === '/api/runs' && init?.method === 'POST'
        ? new Response(JSON.stringify({ detail: 'Input is outside the allowed roots' }), {
            status: 422,
            headers: { 'Content-Type': 'application/json' }
          })
        : undefined
    );
    const wrapper = mount(App);
    await flushPromises();
    await wrapper.get('input#input').setValue('/bad/board.kicad_pcb');
    await wrapper.get('.confirm input').setValue(true);
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(wrapper.get('[role="alert"]').text()).toContain('outside the allowed roots');
  });
});
