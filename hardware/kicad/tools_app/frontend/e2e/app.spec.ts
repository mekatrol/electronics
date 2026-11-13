import { expect, test } from '@playwright/test';

test('loads backend modules and opens readiness', async ({ page }) => {
  const settings = {
    allowed_roots: ['/projects'], python_executable: '/python', kicad_executable: 'kicad',
    kicad_cli_executable: 'kicad-cli', max_concurrent_runs: 2, history_limit: 200, frontend_origin: 'http://localhost:5173',
  };
  const health = {
    status: 'ok', python: { configured: '/python', available: true, resolved: '/python' },
    kicad: { configured: 'kicad', available: false, resolved: null },
    kicad_cli: { configured: 'kicad-cli', available: true, resolved: '/kicad-cli' },
    kipy_importable: true, kicad_api_socket: null, pcb_editor_reachable: false,
  };
  await page.route('**/api/**', async (route) => {
    const path = new URL(route.request().url()).pathname;
    const body = path === '/api/modules' ? [{
      id: 'report', name: 'Board report', description: 'Inspect the board.', category: 'analysis', execution_type: 'read_only',
      requires_kicad: true, requires_pcb_editor: true, requires_kicad_api: true, timeout_seconds: 60, parameters: [],
      risk: { level: 'low', summary: 'Read only.', confirmation_required: false },
    }] : path === '/api/runs' ? [] : path === '/api/health' ? health : settings;
    await route.fulfill({ json: body });
  });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Board report' })).toBeVisible();
  await page.getByRole('button', { name: 'Readiness' }).click();
  await expect(page.getByRole('heading', { name: 'Application readiness' })).toBeVisible();
  await expect(page.getByText('PCB Editor API')).toBeVisible();
});
