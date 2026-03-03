import GLib from 'gi://GLib';

/**
 * BrightnessModule - FASE 4
 *
 * Módulo isolado para controle de brilho via xrandr.
 *
 * NOTA: NÃO integrado ao menu ainda (FASE 5).
 */

export const BrightnessModule = class {
    constructor() {
        this._output = this._detectPrimaryOutput();
        console.log(`[BrightnessModule] Initialized with output: ${this._output}`);
    }

    /**
     * Detecta o monitor primary conectado.
     * Retorna o nome da saída (ex: "DP-2").
     */
    _detectPrimaryOutput() {
        try {
            const [ok, stdout] = GLib.spawn_command_line_sync('xrandr --query');

            if (!ok || !stdout) {
                console.error('[BrightnessModule] Failed to run xrandr --query');
                return null;
            }

            const output = new TextDecoder('utf-8').decode(stdout);
            const lines = output.split('\n');

            // Procurar por linha com "connected primary"
            for (const line of lines) {
                if (line.includes('connected primary')) {
                    const match = line.match(/^(\S+)\s+connected primary/);
                    if (match && match[1]) {
                        return match[1];
                    }
                }
            }

            // Fallback: primeiro monitor conectado
            for (const line of lines) {
                if (line.includes(' connected ') && !line.includes('disconnected')) {
                    const match = line.match(/^(\S+)\s+connected/);
                    if (match && match[1]) {
                        console.warn('[BrightnessModule] No primary output found, using: ' + match[1]);
                        return match[1];
                    }
                }
            }

            console.error('[BrightnessModule] No connected output found');
            return null;

        } catch (e) {
            console.error('[BrightnessModule] Error detecting output: ' + e.message);
            return null;
        }
    }

    /**
     * Obtém o brilho atual (0.0 a 1.0).
     * Retorna null em caso de erro.
     */
    getBrightness() {
        if (!this._output) {
            console.error('[BrightnessModule] No output available');
            return null;
        }

        try {
            const [ok, stdout] = GLib.spawn_command_line_sync('xrandr --verbose');

            if (!ok || !stdout) {
                console.error('[BrightnessModule] Failed to run xrandr --verbose');
                return null;
            }

            const output = new TextDecoder('utf-8').decode(stdout);
            const lines = output.split('\n');

            // Procurar por "Brightness: X.XX" na seção do nosso output
            let inOutputSection = false;
            for (const line of lines) {
                // Entrar na seção do output quando encontramos o nome
                if (line.startsWith(this._output + ' connected') ||
                    line.startsWith(this._output + ' disconnected')) {
                    inOutputSection = true;
                    continue;
                }

                // Sair da seção quando encontramos outro output
                if (inOutputSection && /^[^\s]+\s+(connected|disconnected)/.test(line)) {
                    break;
                }

                // Procurar por Brightness dentro da seção do output
                if (inOutputSection) {
                    const brightnessMatch = line.match(/^\s*Brightness:\s*([\d.]+)/);
                    if (brightnessMatch) {
                        const value = parseFloat(brightnessMatch[1]);
                        console.log(`[BrightnessModule] Current brightness: ${value}`);
                        return value;
                    }
                }
            }

            console.error('[BrightnessModule] Could not find brightness value');
            return null;

        } catch (e) {
            console.error('[BrightnessModule] Error getting brightness: ' + e.message);
            return null;
        }
    }

    /**
     * Define o brilho (0.0 a 1.0).
     * Valores fora de range são clamped.
     * Retorna true em sucesso, false em erro.
     */
    setBrightness(value) {
        if (!this._output) {
            console.error('[BrightnessModule] No output available');
            return false;
        }

        // Clamp value entre 0.1 e 1.0 (evitar 0 que escurece tudo)
        let clamped = Math.max(0.1, Math.min(1.0, value));
        console.log(`[BrightnessModule] Setting brightness to: ${clamped}`);

        try {
            const cmd = `xrandr --output ${this._output} --brightness ${clamped}`;
            const [ok, stdout, stderr] = GLib.spawn_command_line_sync(cmd);

            if (!ok) {
                const errorMsg = stderr ? new TextDecoder('utf-8').decode(stderr) : 'unknown error';
                console.error('[BrightnessModule] Failed to set brightness: ' + errorMsg);
                return false;
            }

            console.log(`[BrightnessModule] Brightness set to: ${clamped}`);
            return true;

        } catch (e) {
            console.error('[BrightnessModule] Error setting brightness: ' + e.message);
            return false;
        }
    }

    /**
     * Obtém o brilho como porcentagem (0 a 100).
     * Retorna null em caso de erro.
     */
    getBrightnessPercent() {
        const value = this.getBrightness();
        if (value === null) {
            return null;
        }
        return Math.round(value * 100);
    }

    /**
     * Define o brilho como porcentagem (0 a 100).
     * Retorna true em sucesso, false em erro.
     */
    setBrightnessPercent(percent) {
        const value = percent / 100;
        return this.setBrightness(value);
    }

    /**
     * Retorna o nome do output detectado.
     */
    getOutputName() {
        return this._output;
    }
};
