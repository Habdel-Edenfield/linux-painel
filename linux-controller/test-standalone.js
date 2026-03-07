#!/usr/bin/env gjs

// Test script for BrightnessModule - runs standalone
// Usage: gjs test-standalone.js

const GLib = imports.gi.GLib;

const BrightnessModule = class {
    constructor() {
        this._output = this._detectPrimaryOutput();
        print(`[BrightnessModule] Initialized with output: ${this._output}`);
    }

    _detectPrimaryOutput() {
        try {
            const [ok, stdout] = GLib.spawn_command_line_sync('xrandr --query');

            if (!ok || !stdout) {
                print('[BrightnessModule] Failed to run xrandr --query');
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
                        print('[BrightnessModule] No primary output found, using: ' + match[1]);
                        return match[1];
                    }
                }
            }

            print('[BrightnessModule] No connected output found');
            return null;

        } catch (e) {
            print('[BrightnessModule] Error detecting output: ' + e.message);
            return null;
        }
    }

    getBrightness() {
        if (!this._output) {
            print('[BrightnessModule] No output available');
            return null;
        }

        try {
            const [ok, stdout] = GLib.spawn_command_line_sync('xrandr --verbose');

            if (!ok || !stdout) {
                print('[BrightnessModule] Failed to run xrandr --verbose');
                return null;
            }

            const output = new TextDecoder('utf-8').decode(stdout);
            const lines = output.split('\n');

            let inOutputSection = false;
            for (const line of lines) {
                if (line.startsWith(this._output + ' connected') ||
                    line.startsWith(this._output + ' disconnected')) {
                    inOutputSection = true;
                    continue;
                }

                if (inOutputSection && /^[^\s]+\s+(connected|disconnected)/.test(line)) {
                    break;
                }

                if (inOutputSection) {
                    const brightnessMatch = line.match(/^\s*Brightness:\s*([\d.]+)/);
                    if (brightnessMatch) {
                        const value = parseFloat(brightnessMatch[1]);
                        print(`[BrightnessModule] Current brightness: ${value}`);
                        return value;
                    }
                }
            }

            print('[BrightnessModule] Could not find brightness value');
            return null;

        } catch (e) {
            print('[BrightnessModule] Error getting brightness: ' + e.message);
            return null;
        }
    }

    setBrightness(value) {
        if (!this._output) {
            print('[BrightnessModule] No output available');
            return false;
        }

        let clamped = Math.max(0.1, Math.min(1.0, value));
        print(`[BrightnessModule] Setting brightness to: ${clamped}`);

        try {
            const cmd = `xrandr --output ${this._output} --brightness ${clamped}`;
            const [ok, stdout, stderr] = GLib.spawn_command_line_sync(cmd);

            if (!ok) {
                const errorMsg = stderr ? new TextDecoder('utf-8').decode(stderr) : 'unknown error';
                print('[BrightnessModule] Failed to set brightness: ' + errorMsg);
                return false;
            }

            print(`[BrightnessModule] Brightness set to: ${clamped}`);
            return true;

        } catch (e) {
            print('[BrightnessModule] Error setting brightness: ' + e.message);
            return false;
        }
    }

    getBrightnessPercent() {
        const value = this.getBrightness();
        if (value === null) {
            return null;
        }
        return Math.round(value * 100);
    }

    setBrightnessPercent(percent) {
        const value = percent / 100;
        return this.setBrightness(value);
    }

    getOutputName() {
        return this._output;
    }
};

// ===== TESTS =====
print('=== BrightnessModule Standalone Test ===\n');

const module = new BrightnessModule();

// Test 1: getOutputName
print(`Test 1 - Output Name: ${module.getOutputName()}`);
print('');

// Test 2: getBrightness
print('Test 2 - Get Current Brightness:');
const current = module.getBrightness();
const percent = module.getBrightnessPercent();
print(`  Raw value: ${current}`);
print(`  Percent: ${percent}%`);
print('');

// Test 3: setBrightnessPercent to 50%
print('Test 3 - Set Brightness to 50%:');
const result50 = module.setBrightnessPercent(50);
print(`  Result: ${result50 ? 'SUCCESS' : 'FAILED'}`);
const new50 = module.getBrightness();
print(`  New value: ${new50} (${module.getBrightnessPercent()}%)`);
print('');

// Test 4: setBrightnessPercent to 80%
print('Test 4 - Set Brightness to 80%:');
const result80 = module.setBrightnessPercent(80);
print(`  Result: ${result80 ? 'SUCCESS' : 'FAILED'}`);
const new80 = module.getBrightness();
print(`  New value: ${new80} (${module.getBrightnessPercent()}%)`);
print('');

// Test 5: setBrightness with clamping
print('Test 5 - Test Clamping (set 150%):');
const resultClamp = module.setBrightnessPercent(150);
print(`  Result: ${resultClamp ? 'SUCCESS' : 'FAILED'}`);
const clamped = module.getBrightness();
print(`  Clamped value: ${clamped} (${module.getBrightnessPercent()}%)`);
print('');

// Restore to 80%
print('Restore to 80%:');
module.setBrightnessPercent(80);

print('\n=== All tests completed ===');
