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
  risk: { level: 'medium', summary: 'Writes a file.' }
};
const settings = {
  allowed_roots: ['/projects'],
  python_executable: '/python',
  kicad_executable: 'kicad',
  kicad_cli_executable: 'kicad-cli',
  max_concurrent_runs: 2,
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
          : url === '/api/runs/latest'
            ? null
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
  it('builds module forms from API metadata without confirmation gating', async () => {
    mockFetch();
    const wrapper = mount(App);
    await flushPromises();
    expect(wrapper.text()).toContain('Panelize PCB');
    expect(wrapper.find('input#input').exists()).toBe(true);
    expect(wrapper.find('input#count').attributes('min')).toBe('1');
    const runButton = wrapper.get('button[type="submit"]');
    expect(runButton.attributes('disabled')).toBeUndefined();
    expect(wrapper.find('.confirm').exists()).toBe(false);
  });

  it('filters modules by a case-insensitive partial name', async () => {
    const inspectionModule = {
      ...moduleDefinition,
      id: 'inspect-board',
      name: 'Inspect Board',
      category: 'analysis'
    };
    mockFetch((url) =>
      url === '/api/modules'
        ? new Response(JSON.stringify([moduleDefinition, inspectionModule]), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
          })
        : undefined
    );
    const wrapper = mount(App);
    await flushPromises();

    const filter = wrapper.get('input[type="search"]');
    await filter.setValue('SPECT bo');

    const moduleButtons = wrapper.findAll('.module-button');
    expect(moduleButtons).toHaveLength(1);
    expect(moduleButtons[0]?.text()).toContain('Inspect Board');
    expect(wrapper.text()).not.toContain('Manufacturing');

    await filter.setValue('missing');
    expect(wrapper.findAll('.module-button')).toHaveLength(0);
    expect(wrapper.text()).toContain('No modules match “missing”.');
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
    await wrapper.get('form').trigger('submit');
    await flushPromises();
    expect(wrapper.get('[role="alert"]').text()).toContain('outside the allowed roots');
  });

  it('allows both validation and fix mode without confirmation', async () => {
    const thermalModule = {
      ...moduleDefinition,
      id: 'validate-thermal-reliefs',
      name: 'Validate Thermal Reliefs',
      parameters: [
        {
          name: 'fix', label: 'Validate and fix', description: 'Fix problems.', kind: 'option',
          flag: '--fix', type: 'boolean', required: false, default: false
        }
      ],
      risk: { level: 'high', summary: 'May change the board.' }
    };
    mockFetch((url) =>
      url === '/api/modules'
        ? new Response(JSON.stringify([thermalModule]), {
            status: 200, headers: { 'Content-Type': 'application/json' }
          })
        : undefined
    );
    const wrapper = mount(App);
    await flushPromises();
    const runButton = wrapper.get('button[type="submit"]');
    expect(runButton.text()).toBe('Validate');
    expect(runButton.attributes('disabled')).toBeUndefined();
    expect(wrapper.find('.confirm').exists()).toBe(false);

    await wrapper.get('input#fix').setValue(true);
    expect(runButton.text()).toBe('Validate and fix');
    expect(runButton.attributes('disabled')).toBeUndefined();
    expect(wrapper.find('.confirm').exists()).toBe(false);
  });

  it('blocks the page while a module runs and only closes after cancellation completes', async () => {
    const running = {
      id: 'run-1', module_id: 'panelize', parameters: {}, status: 'running',
      created_at: '2026-11-20T00:00:00Z', started_at: '2026-11-20T00:00:00Z',
      finished_at: null, exit_code: null, error_summary: null, artifacts: []
    };
    const cancelled = {
      ...running, status: 'cancelled', finished_at: '2026-11-20T00:00:01Z',
      error_summary: 'Cancelled by the user.'
    };
    let finishCancellation: ((response: Response) => void) | undefined;
    let cancellationFinished = false;
    mockFetch((url, init) => {
      if (url === '/api/runs/latest') return new Response(JSON.stringify(running));
      if (url === '/api/runs/run-1')
        return new Response(JSON.stringify(cancellationFinished ? cancelled : running));
      if (url === '/api/runs/run-1/output')
        return new Response(JSON.stringify({ stdout: '', stderr: '' }));
      if (url === '/api/runs/run-1/cancel' && init?.method === 'POST')
        return new Promise<Response>((resolve) => { finishCancellation = resolve; }) as never;
      return undefined;
    });
    const wrapper = mount(App, { attachTo: document.body });
    await flushPromises();

    const overlay = document.body.querySelector<HTMLElement>('.run-overlay');
    expect(overlay).not.toBeNull();
    expect(overlay?.getAttribute('aria-modal')).toBe('true');
    expect(overlay?.textContent).toContain('Running Panelize PCB');
    expect(wrapper.get('.shell').attributes()).toHaveProperty('inert');

    overlay?.click();
    await flushPromises();
    expect(document.body.querySelector('.run-overlay')).not.toBeNull();

    const cancelButton = document.body.querySelector<HTMLButtonElement>('.cancel-run');
    cancelButton?.click();
    await flushPromises();
    expect(cancelButton?.disabled).toBe(true);
    expect(document.body.querySelector('.run-overlay')).not.toBeNull();

    cancellationFinished = true;
    finishCancellation?.(new Response(JSON.stringify(cancelled)));
    await flushPromises();
    expect(document.body.querySelector('.run-overlay')).toBeNull();
    wrapper.unmount();
  });
});
